import logging

from django.conf import settings
from django.db import transaction
from django.db.models.query_utils import Q
from django.utils import timezone

from data_registry.cbom.task.factory import TaskFactory
from data_registry.models import Job, Task

logger = logging.getLogger('cbom')


def process(collection):
    logger.debug("Processing collection {}".format(collection))

    if should_be_planned(collection):
        plan(collection)

    jobs = Job.objects.filter(collection=collection).filter(~Q(status=Job.Status.COMPLETED))

    for job in jobs:
        with transaction.atomic():
            # initiate job context
            if job.context is None:
                job.context = {}
                job.save()

            # list of job tasks sorted by priority
            tasks = Task.objects.filter(job=job).order_by("order")
            run_next_planned = True
            job_complete = True

            for task in tasks:
                # finished task -> no action needed
                if task.status == Task.Status.COMPLETED:
                    continue

                _task = TaskFactory.get_task(collection, job, task)

                try:
                    if task.status in [Task.Status.WAITING, Task.Status.RUNNING]:
                        status = _task.get_status()
                        if status in [Task.Status.WAITING, Task.Status.RUNNING]:
                            # do nothing, the task is still running
                            run_next_planned = False
                            continue
                        elif status == Task.Status.COMPLETED:
                            # complete the task
                            task.end = timezone.now()
                            task.status = Task.Status.COMPLETED
                            task.result = Task.Result.OK

                            logger.debug("Task {} completed".format(task))
                    elif task.status == Task.Status.PLANNED and run_next_planned:
                        if job.status == Job.Status.PLANNED:
                            job.start = timezone.now()
                            job.status = Job.Status.RUNNING
                            job.save()

                            logger.debug("Job {} started".format(job))

                        # run the task
                        _task.run()
                        task.start = timezone.now()
                        task.status = Task.Status.RUNNING
                        run_next_planned = False

                        logger.debug("Task {} started".format(task))

                    task.save()
                    job_complete &= task.status == Task.Status.COMPLETED
                except Exception as e:
                    job_complete = True
                    task.end = timezone.now()
                    task.status = Task.Status.COMPLETED
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    logger.exception(e)
                    break

            # complete the job if all of its tasks are completed
            if job_complete:
                job.status = Job.Status.COMPLETED
                job.end = timezone.now()
                job.save()

                logger.debug("Job {} completed".format(job))


def should_be_planned(collection):
    # frozen collections shouldn't be planned
    if collection.frozen:
        return False

    jobs = Job.objects.filter(collection=collection).filter(~Q(status=Job.Status.COMPLETED))
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

    logger.debug("New job {} planned".format(job))
