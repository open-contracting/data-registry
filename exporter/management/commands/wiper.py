import logging

from django.core.management.base import BaseCommand

from exporter.export.wiper import start

logger = logging.getLogger('wiper')


class Command(BaseCommand):
    help = 'Removes all the exported data'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Wiper started")

        start()
