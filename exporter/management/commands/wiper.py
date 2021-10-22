import logging

from django.core.management.base import BaseCommand

from exporter.export.wiper import start

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Starts a worker to delete the files exported from collections in Kingfisher Process.

    It consumes messages from RabbitMQ, which indicate the path components of the directory tree to delete (consisting
    of the spider name and the job ID).

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Wiper started")

        start()
