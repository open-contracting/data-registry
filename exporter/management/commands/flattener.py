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
    help = """
    Convert JSON files to CSV and Excel files.

    Data is exported as gzipped CSV and Excel files, with one file per year and one full file per format.
    """

    def handle(self, *args, **options):
        consume(
            on_message_callback=callback,
            queue="flattener_init",
            routing_keys=["flattener_init", "flattener_file"],
            # When there's high load, the heartbeat isn't sent, causing "missed heartbeats from client, timeout: 60s"
            # and "closing AMQP connection" in RabbitMQ logs and ConnectionResetError(104, 'Connection reset by peer')
            # in the asynchronous client. Use 1800 seconds to give time for a heartbeat.
            # https://stackoverflow.com/q/70006802/244258
            # https://www.rabbitmq.com/docs/heartbeats#disabling
            rabbit_params={"heartbeat": 1800},  # 30 mins
            decorator=decorator,
        )


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")
    file_path = input_message.get("file_path")

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    if file_path:  # flattener_file
        process_file(job_id, file_path)
    else:  # flattener_init
        for path in Export(job_id).get_convertible_paths():
            publish({"job_id": job_id, "file_path": str(path)}, "flattener_file")


def process_file(job_id, file_path):
    file_name = os.path.basename(file_path)
    stem = file_name[:-9]  # remove .jsonl.gz

    export = Export(job_id, basename=f"{stem}.csv.tar.gz")

    csv_path = export.directory / f"{stem}.csv.tar.gz"
    xlsx_path = export.directory / f"{stem}.xlsx"
    csv_exists = os.path.isfile(csv_path)
    xlsx_exists = os.path.isfile(xlsx_path)
    csv = False
    xlsx = False

    if csv_exists and xlsx_exists:
        logger.debug("Already done job_id=%s file_path=%s", job_id, file_path)
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
                logger.debug("CSV already done and XLSX limit exceeded job_id=%s file_path=%s", job_id, file_path)
                return

            output = flatterer_flatten(file_path, str(infile), str(outdir), csv=csv, xlsx=xlsx)

            if csv:
                with tarfile.open(csv_path, "w:gz") as tar:
                    tar.add(outdir / "csv", arcname=infile.stem)  # remove .jsonl
            if xlsx and "xlsx" in output:
                shutil.move(output["xlsx"], xlsx_path)
    # EOFError: Compressed file ended before the end-of-stream marker was reached
    # FileNotFoundError: https://github.com/open-contracting/data-registry/issues/254
    except (EOFError, FileNotFoundError) as e:
        logger.warning("%s job_id=%s file_path=%s", e, job_id, file_path)
        # The message has already been ack'd, so it can't be nack'd with requeue=True.
        if isinstance(e, EOFError):
            publish({"job_id": job_id, "file_path": file_path}, "flattener_file")
        # Only delete any files whose creation was attempted.
        for path, attempt in ((csv_path, csv), (xlsx_path, xlsx)):
            if attempt:
                Path(path).unlink(missing_ok=True)
    else:
        logger.debug("Done job_id=%s file_path=%s", job_id, file_path)
    finally:
        export.unlock()


def flatterer_flatten(file_path, infile, outdir, *, csv=False, xlsx=False, threads=0):
    """
    Convert the file from JSON to CSV and Excel.

    If an error occurs:

    -  If ``xlsx=True`` and ``csv=True``, attempt with ``xlsx=False``.
    -  If ``xlsx=True`` and ``csv=False``, log the error and return.
    -  Otherwise (``csv=True``), re-raise the error.
    """
    try:
        return flatterer.flatten(infile, outdir, csv=csv, xlsx=xlsx, ndjson=True, force=True, threads=threads)
    except RuntimeError as e:
        if not xlsx:  # CSV-only should succeed.
            raise
        if not csv:  # Excel-only may fail.
            logger.exception("Failed Excel-only conversion of %s", file_path)
            return {}
        if "Number of rows is too large for XLSX file" in str(e):
            logger.warning("%s %s (will attempt CSV-only conversion)", e, file_path)
        else:
            logger.exception("Failed full conversion of %s (will attempt CSV-only conversion)", file_path)
        return flatterer_flatten(file_path, infile, outdir, csv=csv, xlsx=False, threads=threads)
