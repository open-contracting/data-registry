import logging

from django.core.management.base import BaseCommand

from data_registry.exceptions import RecoverableException
from data_registry.models import Collection, Job
from data_registry.process_manager import get_task_manager, process

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Orchestrate and evaluate all jobs and tasks"

    def handle(self, *args, **options):
        for collection in Collection.objects.all():
            process(collection)

        # Complete jobs, whose temporary data isn't to be preserved or already deleted.
        for job in Job.objects.prefetch_related("task_set").complete().filter(keep_all_data=False, archived=False):
            for task in job.task_set.all():
                task_manager = get_task_manager(task)
                if not task_manager.final_output:
                    try:
                        task_manager.wipe()
                    except RecoverableException:
                        logger.exception("Recoverable exception when wiping task %s for job %s", task, job)
                        break
            else:
                job.archived = True
                job.save(update_fields=["modified", "archived"])
                logger.info("Job %s wiped", job)
