import logging

from django.conf import settings
from django.db.models.query_utils import Q
from django.utils import timezone

from data_registry.cbom.tasks import TaskFactory
from data_registry.models import Job, Task

logger = logging.getLogger('cbom')


def process(collection):
    logger.debug("Processing collection {}".format(collection))

    if should_be_planned(collection):
        plan(collection)

    jobs = Job.objects.filter(collection=collection).filter(~Q(status="COMPLETED"))

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
                        task.end = timezone.now()
                        task.status = "COMPLETED"
                        task.result = "OK"
                elif task.status == "PLANNED" and run_next_planned:
                    if job.status == "PLANNED":
                        job.start = timezone.now()
                        job.status = "RUNNNIG"
                        job.save()

                    # run task
                    _task.run()
                    task.start = timezone.now()
                    task.status = "RUNNING"
                    run_next_planned = False

                task.save()
                job_complete &= task.status == "COMPLETED"
            except Exception as e:
                job_complete = True
                task.end = timezone.now()
                task.status = "COMPLETED"
                task.result = "FAILED"
                task.note = str(e)
                task.save()
                break

        if job_complete:
            job.status = "COMPLETED"
            job.end = timezone.now()
            job.save()


def should_be_planned(collection):
    jobs = Job.objects.filter(collection=collection)
    if not jobs:
        return True
    else:
        return False


def plan(collection):
    if not settings.JOB_TASKS_PLAN:
        raise Exception("JOB_TASKS_PLAN is not set")

    job = collection.job.create(
        start=timezone.now(),
        status="PLANNED"
    )

    tasks = settings.JOB_TASKS_PLAN

    for i, t in enumerate(tasks, start=1):
        job.task.create(status="PLANNED", type=t, order=i)
