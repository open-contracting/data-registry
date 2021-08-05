import logging

from django.core.management.base import BaseCommand

from data_registry.cbom.process import process
from data_registry.cbom.task.pelican import Pelican
from data_registry.cbom.task.process import Process
from data_registry.cbom.task.scrape import Scrape
from data_registry.models import Collection, Job

logger = logging.getLogger('cbom')


class Command(BaseCommand):
    help = 'Process, orchestrate and evaluate all jobs and tasks in data registry'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("CBOM started")

        for collection in Collection.objects.all():
            process(collection)

        # wipe jobs data
        wiped_jobs = Job.objects.filter(status=Job.Status.COMPLETED, keep_all_data=False, archived=False)
        for job in wiped_jobs:
            self.wipe_job(job)
            job.archived = True
            job.save()

            logger.info(f"Job #{job.id} wiped")

    def wipe_job(self, job):
        if not job:
            return

        Scrape(job.collection, job).wipe()
        Process(job).wipe()
        Pelican(job).wipe()
