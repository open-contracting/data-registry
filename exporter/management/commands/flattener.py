import gzip
import logging
import os
import shutil
import tarfile

import flatterer
from django.conf import settings
from django.core.management.base import BaseCommand
from yapw.methods.blocking import ack

from exporter.util import Export, consume

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Start a worker to flatten JSON files.

    Data is exported as gzipped CSV and Excel files, with one file per year and one ``full.[csv|xlsx].gz`` file.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(callback, "flattener_init")


def callback(state, channel, method, properties, input_message):
    job_id = 10

    export = Export(job_id, export_type="flat")
    export.lock()
    # acknowledge message processing now to avoid connection loses
    # the rest can run for hours and is irreversible anyway
    ack(state, channel, method.delivery_tag)

    for file in os.listdir(export.directory):
        if file.endswith(".jsonl.gz"):
            with gzip.open(os.path.join(export.directory, file), "rb") as compressed:
                json_path = os.path.join(export.directory, f"{file.replace('.gz', '')}.jsonl")
                with open(json_path, "wb") as tmp_json_file:
                    shutil.copyfileobj(compressed, tmp_json_file)
                    flatten_and_package_file(json_path, export.directory)
                os.remove(json_path)

    export.unlock()


def flatten_and_package_file(path, directory):
    if os.path.getsize(path) < settings.EXPORTER_MAX_JSON_BYTES_TO_EXCEL:
        excel = True
    else:
        excel = False
    tmp_flatten_dir = os.path.join(directory, "flatten")
    output = flatterer.flatten(str(path), tmp_flatten_dir, xlsx=excel, json_stream=True, force=True)
    base_name = str(path).replace(".jsonl", "")
    # Excel file gz
    if excel:
        with open(output["xlsx"], "rb") as excel_file:
            with gzip.open(f"{base_name}.xlsx.gz", "wb") as packaged_excel:
                shutil.copyfileobj(excel_file, packaged_excel)
    # CSV folder tar.gz
    csv_folder = os.path.join(tmp_flatten_dir, "csv")
    with tarfile.open(f"{base_name}.csv.tar.gz", "w:gz") as tar:
        tar.add(csv_folder, arcname=os.path.basename(base_name))

    shutil.rmtree(tmp_flatten_dir)
