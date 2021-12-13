import logging

from django.core.management.base import BaseCommand

from data_registry.models import Collection, Job
from data_registry.process_manager.process import process
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process, orchestrate and evaluate all jobs and tasks in data registry"

    def handle(self, *args, **options):
        for collection in Collection.objects.all():
            process(collection)

        wiped_jobs = Job.objects.filter(status=Job.Status.COMPLETED, keep_all_data=False, archived=False)
        for job in wiped_jobs:
            self.wipe_job(job)
            job.archived = True
            job.save()

            logger.info("Job #%s wiped", job.id)

    def wipe_job(self, job):
        if not job:
            return

        Collect(job.collection, job).wipe()
        Process(job).wipe()
        Pelican(job).wipe()