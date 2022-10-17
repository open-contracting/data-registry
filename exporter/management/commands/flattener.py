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
from yapw.methods.blocking import ack

from exporter.util import Export, consume, decorator, publish

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Start a worker to flatten JSON files.

    Data is exported as gzipped CSV and Excel files, with one file per year and one full file per format.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(callback, "flattener_init", ["flattener_init", "flattener_file"], decorator=decorator)


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")
    file_path = input_message.get("file_path")

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    if file_path:
        process_file(file_path, job_id)
    else:
        publish_file(job_id)


def publish_file(job_id):
    export = Export(job_id, export_type="flat")
    for entry in os.scandir(export.directory):
        if not entry.name.endswith(".jsonl.gz") or "_" in entry.name:  # don't process months at the moment
            continue
        publish({"job_id": job_id, "file_path": entry.path}, "flattener_file")


def process_file(file_path, job_id):
    file_name = Path(file_path).name

    export = Export(job_id, export_type="flat", lockfile_suffix=file_name)

    final_path_prefix = file_path[:-9]  # remove .jsonl.gz

    csv_path = f"{final_path_prefix}.csv.tar.gz"
    xlsx_path = f"{final_path_prefix}.xlsx"

    if os.path.isfile(xlsx_path) and os.path.isfile(csv_path):
        return

    export.lock()

    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            infile = tmpdir / file_name[:-3]  # remove .gz
            outdir = tmpdir / "flatten"  # force=True deletes this directory

            with gzip.open(file_path) as i:
                with infile.open("wb") as o:
                    shutil.copyfileobj(i, o)

            xlsx = infile.stat().st_size < settings.EXPORTER_MAX_JSON_BYTES_TO_EXCEL and not os.path.isfile(xlsx_path)
            csv = not os.path.isfile(csv_path)
            output = flatterer_flatten(export, str(infile), str(outdir), xlsx=xlsx, csv=csv)

            if xlsx and "xlsx" in output:
                shutil.move(output["xlsx"], xlsx_path)
            if csv:
                with tarfile.open(csv_path, "w:gz") as tar:
                    tar.add(outdir / "csv", arcname=infile.stem)  # remove .jsonl
    except FileNotFoundError:
        for path in [xlsx_path, csv_path]:
            Path(path).unlink(missing_ok=True)
    finally:
        export.unlock()


def flatterer_flatten(export, infile, outdir, xlsx=False, csv=True):
    """
    Convert the file from JSON to CSV and Excel.

    If an error occurs:

    -  If ``xlsx=True``, attempt with ``xlsx=False``.
    -  Otherwise, re-raise the error.
    """
    try:
        if csv or xlsx:
            return flatterer.flatten(infile, outdir, csv=csv, xlsx=xlsx, json_stream=True, force=True)
    except RuntimeError:
        if xlsx:
            logger.exception("Attempting CSV-only conversion in %s (max_rows_lower_bound=%s)", export)
            return flatterer_flatten(export, infile, outdir)
        raise
