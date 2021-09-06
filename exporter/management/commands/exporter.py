import logging

from django.core.management.base import BaseCommand

from exporter.export.worker import start

logger = logging.getLogger('exporter')


class Command(BaseCommand):
    """
    Starts a worker to export files from collections in Kingfisher Process.

    It consumes messages from RabbitMQ, which indicate the collection to export and the path components of the
    directory to write to (consisting of the spider name and the job ID).

    Data is exported as gzipped line-delimited JSON files, with one file per year and one ``full.jsonl.gz`` file.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Exporter started")

        start()
