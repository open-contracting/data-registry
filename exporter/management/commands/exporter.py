import logging

from django.core.management.base import BaseCommand

from exporter.export.worker import start

logger = logging.getLogger('exporter')


class Command(BaseCommand):
    help = 'Process, orchestrate and evaluate all jobs and tasks in data registry'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("Exporter started")

        start()
