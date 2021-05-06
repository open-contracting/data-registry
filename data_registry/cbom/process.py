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

    jobs = Job.objects.filter(collection=collection).filter(~Q(status=Job.Status.COMPLETED))

    for job in jobs:
        tasks = Task.objects.filter(job=job).order_by("order")
        run_next_planned = True
        job_complete = True

        for task in tasks:
            # finished task -> no action needed
            if task.status == Task.Status.COMPLETED:
                continue

            _task = TaskFactory.get_task(job, task)

            try:
                if task.status in [Task.Status.WAITING, Task.Status.RUNNING]:
                    if _task.get_status() in [Task.Status.WAITING, Task.Status.RUNNING]:
                        run_next_planned = False
                        continue
                    else:
                        task.end = timezone.now()
                        task.status = Task.Status.COMPLETED
                        task.result = Task.Result.OK
                elif task.status == Task.Status.PLANNED and run_next_planned:
                    if job.status == Job.Status.PLANNED:
                        job.start = timezone.now()
                        job.status = Job.Status.RUNNING
                        job.save()

                    # run task
                    _task.run()
                    task.start = timezone.now()
                    task.status = Task.Status.RUNNING
                    run_next_planned = False

                task.save()
                job_complete &= task.status == Task.Status.COMPLETED
            except Exception as e:
                job_complete = True
                task.end = timezone.now()
                task.status = Task.Status.COMPLETED
                task.result = Task.Result.FAILED
                task.note = str(e)
                task.save()
                break

        if job_complete:
            job.status = Job.Status.COMPLETED
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
        status=Job.Status.PLANNED
    )

    tasks = settings.JOB_TASKS_PLAN

    for i, t in enumerate(tasks, start=1):
        job.task.create(status=Task.Status.PLANNED, type=t, order=i)
