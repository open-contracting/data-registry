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

from data_registry.models import Job
from exporter.util import Export, consume, decorator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Start a worker to flatten JSON files.

    Data is exported as gzipped CSV and Excel files, with one file per year and one full file per format.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(callback, "flattener_init", decorator=decorator)


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")
    max_rows_lower_bound = Job.objects.get(id=job_id).get_max_rows_lower_bound()

    export = Export(job_id, export_type="flat")
    export.lock()

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    for entry in os.scandir(export.directory):
        if not entry.name.endswith(".jsonl.gz") or "_" in entry.name:  # don't process months at the moment
            continue

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            tmpfile = tmpdir / entry.name[:-3]  # remove .gz
            outpath = entry.path[:-9]  # remove .jsonl.gz

            with gzip.open(entry.path) as infile:
                with tmpfile.open("wb") as outfile:
                    shutil.copyfileobj(infile, outfile)

            # For max_rows_lower_bound, see https://github.com/kindly/libflatterer/issues/1
            xlsx = tmpfile.stat().st_size < settings.EXPORTER_MAX_JSON_BYTES_TO_EXCEL and max_rows_lower_bound < 65536
            output = flatterer_flatten(export, str(tmpfile), tmpdirname, xlsx)

            if "xlsx" in output:
                shutil.move(output["xlsx"], f"{outpath}.xlsx")

            with tarfile.open(f"{outpath}.csv.tar.gz", "w:gz") as tar:
                tar.add(tmpdir / "csv", arcname=tmpfile.stem)  # remove .jsonl

    export.unlock()


def flatterer_flatten(export, infile, outdir, xlsx):
    """
    Convert the file from JSON to CSV and Excel.

    If an error occurs:

    -  If ``xlsx=True``, attempt with ``xlsx=False``.
    -  Otherwise, unlock the export and re-raise the error.
    """
    try:
        return flatterer.flatten(infile, outdir, xlsx=xlsx, json_stream=True, force=True)
    except RuntimeError:
        if xlsx:
            logger.exception("Attempting CSV-only conversion after failing CSV+Excel conversion in %s", export)
            return flatterer_flatten(export, infile, outdir, False)

        # The lock prevents multiple threads from creating the same files in the export directory. Since we
        # re-raise the error before writing those files, we can unlock here.
        export.unlock()
        raise
