from django.core.management.base import BaseCommand

from data_registry.exceptions import RecoverableException
from data_registry.models import Collection, Job
from data_registry.process_manager.process import get_task_manager, process


class Command(BaseCommand):
    help = "Orchestrate and evaluate all jobs and tasks"

    def handle(self, *args, **options):
        for collection in Collection.objects.all():
            process(collection)

        for job in Job.objects.prefetch_related("task").complete().filter(keep_all_data=False, archived=False):
            for task in job.task_set.all():
                task_manager = get_task_manager(task)
                if not task_manager.final_output:
                    try:
                        task_manager.wipe()
                    except RecoverableException:
                        self.stderr.write(f"Recoverable exception when wiping task {task} for job {job}")
                        break
            else:
                job.archived = True
                job.save()
                # https://docs.djangoproject.com/en/4.2/ref/django-admin/#cmdoption-verbosity
                if options["verbosity"] > 1:
                    self.stdout.write(f"Job {job} wiped")
