import gzip
import logging
import os
import shutil
import tarfile
import tempfile
from pathlib import Path

import flatterer
from django.conf import settings
from django.core.management.base import BaseCommand
from yapw.methods import ack

from exporter.util import Export, consume, decorator, publish

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Start a worker to flatten JSON files.

    Data is exported as gzipped CSV and Excel files, with one file per year and one full file per format.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(
            on_message_callback=callback,
            queue="flattener_init",
            routing_keys=["flattener_init", "flattener_file"],
            # Witnessed "AMQPHeartbeatTimeout: No activity or too many missed heartbeats in the last 60 seconds."
            # while using Pika's BlockingConnection when processing the largest files.
            rabbit_params={"heartbeat": 0},
            decorator=decorator,
        )


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")
    file_path = input_message.get("file_path")

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    if file_path:
        process_file(job_id, file_path)
    else:
        publish_file(job_id)


def publish_file(job_id):
    export = Export(job_id)
    for entry in os.scandir(export.directory):
        if not entry.name.endswith(".jsonl.gz") or "_" in entry.name:  # don't process YYYY_MM files
            continue
        publish({"job_id": job_id, "file_path": entry.path}, "flattener_file")


def process_file(job_id, file_path):
    file_name = os.path.basename(file_path)
    stem = file_name[:-9]  # remove .jsonl.gz

    export = Export(job_id, basename=f"{stem}.csv.tar.gz")

    csv_path = export.directory / f"{stem}.csv.tar.gz"
    xlsx_path = export.directory / f"{stem}.xlsx"
    csv_exists = os.path.isfile(csv_path)
    xlsx_exists = os.path.isfile(xlsx_path)

    if csv_exists and xlsx_exists:
        return

    export.lock()

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            infile = tmpdir / file_name[:-3]  # remove .gz
            outdir = tmpdir / "flatten"  # force=True deletes this directory

            # flatterer has a gzip_input option. To skip decompression here, we would need to change the
            # `EXPORTER_MAX_JSON_BYTES_TO_EXCEL` line below.
            with gzip.open(file_path) as i, infile.open("wb") as o:
                shutil.copyfileobj(i, o)

            csv = not csv_exists
            xlsx = not xlsx_exists and infile.stat().st_size < settings.EXPORTER_MAX_JSON_BYTES_TO_EXCEL

            if not csv and not xlsx:
                return

            # flatterer is broken when multithreading.
            # https://github.com/kindly/flatterer/issues/53
            threads = 1

            # Count JSON lines up to the number of CPUs.
            # https://github.com/kindly/flatterer/issues/46
            # threads = 0
            # max_threads = multiprocessing.cpu_count()
            # with infile.open() as f:
            #     for _ in f:
            #         threads += 1
            #         if threads >= max_threads:
            #             break

            output = flatterer_flatten(export, str(infile), str(outdir), csv=csv, xlsx=xlsx, threads=threads)

            if csv:
                with tarfile.open(csv_path, "w:gz") as tar:
                    tar.add(outdir / "csv", arcname=infile.stem)  # remove .jsonl
            if xlsx and "xlsx" in output:
                shutil.move(output["xlsx"], xlsx_path)
    # https://github.com/open-contracting/data-registry/issues/254
    except FileNotFoundError:
        # Only delete any files whose creation was attempted.
        for path, exists in ((csv_path, csv_exists), (xlsx_path, xlsx_exists)):
            if not exists:
                Path(path).unlink(missing_ok=True)
    finally:
        export.unlock()


def flatterer_flatten(export, infile, outdir, csv=False, xlsx=False, threads=0):
    """
    Convert the file from JSON to CSV and Excel.

    If an error occurs:

    -  If ``xlsx=True`` and ``csv=True``, attempt with ``xlsx=False``.
    -  If ``xlsx=True`` and ``csv=False``, log the error and return.
    -  Otherwise (``csv=True``), re-raise the error.
    """
    try:
        return flatterer.flatten(infile, outdir, csv=csv, xlsx=xlsx, ndjson=True, force=True, threads=threads)
    except RuntimeError:
        if not xlsx:  # CSV-only should succeed.
            raise
        if not csv:  # Excel-only may fail.
            logger.exception("Failed Excel-only conversion in %s", export)
            return {}
        logger.exception("Attempting CSV-only conversion in %s", export)
        return flatterer_flatten(export, infile, outdir, csv=csv, xlsx=False, threads=threads)
