import logging

from django.core.management.base import BaseCommand

from exporter.export.wiper import start

logger = logging.getLogger('wiper')


class Command(BaseCommand):
    """
    Starts wiper worker (connects to rabbitmq and consumes messages) responsible for removal
    of previously exported data. Removes data of particular job (defined in message) only.

    It's safe to run multiple workers of this type at the same type.
    """

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Wiper started")

        start()
