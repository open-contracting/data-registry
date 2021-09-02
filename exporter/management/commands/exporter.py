import logging

from django.core.management.base import BaseCommand

from exporter.export.worker import start

logger = logging.getLogger('exporter')


class Command(BaseCommand):
    """
    Starts exporter worker (connects to rabbitmq and consumes messages) responsible for export of the
    data from kingfisher-process db. Zipped data are stored in predefined directory structure and
    either downloaded directly or sent to flatten tool to be further processed.

    It's safe to run multiple workers of this type at the same type.
    """

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Exporter started")

        start()
