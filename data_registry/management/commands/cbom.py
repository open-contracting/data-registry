import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models.query_utils import Q

from data_registry.management.commands.tasks import TaskFactory
from data_registry.models import Collection, Job, Task

logger = logging.getLogger('cbom')


class Command(BaseCommand):
    help = 'Process, orchestrate and evaluate all jobs and tasks in data registry'

    def handle(self, *args, **options):
        logging.captureWarnings(True)
        logger.info("CBOM started")

        for collection in Collection.objects.all():
            jobs = Job.objects.filter(collection=collection).filter(~Q(status="COMPLETED"))

            # CREATE NEW JOB
            if not jobs:
                job = collection.job.create(
                    start=datetime.now(),
                    status="PLANNED"
                )

                job.task.create(status="PLANNED", type="test", order=1)
                job.task.create(status="PLANNED", type="test", order=2)

                jobs = [job]

            for job in jobs:
                tasks = Task.objects.filter(job=job).order_by("order")
                run_next_planned = True
                job_complete = True

                for task in tasks:
                    # finished task -> no action needed
                    if task.status == "COMPLETED":
                        continue

                    _task = TaskFactory.get_task(job, task)

                    try:
                        if task.status in ["WAITING", "RUNNING"]:
                            if _task.get_status() in ["WAITING", "RUNNING"]:
                                run_next_planned = False
                                continue
                            else:
                                task.end = datetime.now()
                                task.status = "COMPLETED"
                                task.result = "OK"
                        elif task.status == "PLANNED" and run_next_planned:
                            if job.status == "PLANNED":
                                job.start = datetime.now()
                                job.status = "RUNNNIG"
                                job.save()

                            # run task
                            _task.run()
                            task.start = datetime.now()
                            task.status = "RUNNING"
                            run_next_planned = False

                        task.save()
                        job_complete &= task.status == "COMPLETED"
                    except Exception as e:
                        job_complete = True
                        task.end = datetime.now()
                        task.status = "COMPLETED"
                        task.result = "FAILED"
                        task.note = str(e)
                        task.save()
                        break

                if job_complete:
                    job.status = "COMPLETED"
                    job.end = datetime.now()
                    job.save()
