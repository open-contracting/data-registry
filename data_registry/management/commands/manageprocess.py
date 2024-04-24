import logging

from django.core.management.base import BaseCommand

from data_registry.models import Collection, Job
from data_registry.process_manager.process import get_task_manager, process

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process, orchestrate and evaluate all jobs and tasks in data registry"

    def handle(self, *args, **options):
        for collection in Collection.objects.all():
            process(collection)

        for job in Job.objects.select_related("task").filter(
            status=Job.Status.COMPLETED, keep_all_data=False, archived=False
        ):
            for task in job.task.all():
                task_manager = get_task_manager(task)
                if not task_manager.final_output:
                    task_manager.wipe()

            job.archived = True
            job.save()

            logger.info("Job #%s wiped", job.id)
