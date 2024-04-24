import logging
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Case, When
from django.db.models.functions import Now

from data_registry.exceptions import RecoverableException
from data_registry.models import Collection, Job, Task
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process

logger = logging.getLogger(__name__)


def get_runner(job, task):
    match task.type:
        case Task.Type.COLLECT:
            return Collect(job)
        case Task.Type.PROCESS:
            return Process(job)
        case Task.Type.PELICAN:
            return Pelican(job)
        case Task.Type.EXPORTER:
            return Exporter(job)
        case Task.Type.FLATTENER:
            return Flattener(job)
        case _:
            raise Exception("Unsupported task type")


def process(collection):
    if should_be_planned(collection):
        plan(collection)

    jobs = collection.job.exclude(status=Job.Status.COMPLETED)

    for job in jobs:
        with transaction.atomic():
            job_complete = True

            for task in job.task.order_by("order"):
                # finished task -> no action needed
                if task.status == Task.Status.COMPLETED:
                    continue

                runner = get_runner(job, task)

                try:
                    if task.status in (Task.Status.WAITING, Task.Status.RUNNING):
                        status = runner.get_status()
                        logger.debug("Task %s is %s (%s: %s)", task, status, collection.country, collection)
                        if status in (Task.Status.WAITING, Task.Status.RUNNING):
                            # Reset the task, in case it has recovered.
                            job_complete = False
                            task.result = ""
                            task.note = ""
                            task.save()
                            break
                        elif status == Task.Status.COMPLETED:
                            task.end = Now()
                            task.status = Task.Status.COMPLETED
                            task.result = Task.Result.OK
                            task.save()
                    elif task.status == Task.Status.PLANNED:
                        if job.status == Job.Status.PLANNED:
                            job.start = Now()
                            job.status = Job.Status.RUNNING
                            job.save()

                            logger.debug("Job %s is starting (%s: %s)", job, collection.country, collection)

                        runner.run()

                        task.start = Now()
                        task.status = Task.Status.RUNNING
                        task.save()

                        job_complete = False

                        logger.debug("Task %s is starting (%s: %s)", task, collection.country, collection)

                        break
                except RecoverableException as e:
                    job_complete = False
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    logger.exception(e)
                    break
                except Exception as e:
                    job_complete = False

                    logger.exception(e)

                    # close task as failed
                    task.end = Now()
                    task.status = Task.Status.COMPLETED
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    # close job
                    job.end = Now()
                    job.status = Job.Status.COMPLETED
                    job.save()

                    logger.warning("Job %s has failed (%s: %s)", job, collection.country, collection)
                    break

            # complete the job if all of its tasks are completed
            if job_complete:
                job.status = Job.Status.COMPLETED
                job.end = Now()
                job.save()

                collection.last_retrieved = job.task.get(type=settings.JOB_TASKS_PLAN[0]).end
                collection.save()

                # set active job
                collection.job.update(
                    active=Case(When(id=job.id, then=True), default=False, output_field=BooleanField())
                )

                logger.debug("Job %s has completed (%s: %s)", job, collection.country, collection)


def should_be_planned(collection):
    # frozen collections shouldn't be planned
    if collection.frozen:
        return False

    jobs = collection.job.exclude(status=Job.Status.COMPLETED)
    if not jobs:
        # update frequency is not set, plan next job
        if not collection.retrieval_frequency:
            return True

        # plan next job depending on update frequency
        last_job = collection.job.filter(status=Job.Status.COMPLETED).order_by("-start").first()
        if not last_job:
            return True

        delta = timedelta(days=30)  # MONTHLY
        if collection.retrieval_frequency == Collection.RetrievalFrequency.HALF_YEARLY:
            delta = timedelta(days=180)
        elif collection.retrieval_frequency == Collection.RetrievalFrequency.ANNUALLY:
            delta = timedelta(days=365)

        return date.today() >= (last_job.start + delta).date()
    else:
        return False


def plan(collection):
    if not settings.JOB_TASKS_PLAN:
        raise Exception("JOB_TASKS_PLAN is not set")

    job = collection.job.create(start=Now(), status=Job.Status.PLANNED)

    for order, task_type in enumerate(settings.JOB_TASKS_PLAN, start=1):
        job.task.create(status=Task.Status.PLANNED, type=task_type, order=order)

    logger.debug("New job %s planned", job)
