import logging
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from data_registry.models import Collection, Job, Task

logger = logging.getLogger('cbom')


class Command(BaseCommand):
    help = 'Process, orchestrate and evaluate all jobs and tasks in data registry'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("CBOM started")

        for collection in Collection.objects.all():
            processcollection

