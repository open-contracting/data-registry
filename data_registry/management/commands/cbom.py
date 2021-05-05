import logging

from django.core.management.base import BaseCommand

from data_registry.cbom.process import process
from data_registry.models import Collection

logger = logging.getLogger('cbom')


class Command(BaseCommand):
    help = 'Process, orchestrate and evaluate all jobs and tasks in data registry'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("CBOM started")

        for collection in Collection.objects.all():
            process(collection)
