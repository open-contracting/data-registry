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


def get_task_manager(task):
    match task.type:
        case Task.Type.COLLECT:
            return Collect(task)
        case Task.Type.PROCESS:
            return Process(task)
        case Task.Type.PELICAN:
            return Pelican(task)
        case Task.Type.EXPORTER:
            return Exporter(task)
        case Task.Type.FLATTENER:
            return Flattener(task)
        case _:
            raise Exception("Unsupported task type")


def process(collection):
    if should_be_planned(collection):
        plan(collection)

    country = collection.country

    for job in collection.job.exclude(status=Job.Status.COMPLETED):
        with transaction.atomic():
            for task in job.task.exclude(status=Task.Status.COMPLETED).order_by("order"):
                task_manager = get_task_manager(task)

                try:
                    match task.status:
                        case Task.Status.PLANNED:
                            # If this is the first task...
                            if job.status == Job.Status.PLANNED:
                                job.initiate()
                                logger.debug("Job %s is starting (%s: %s)", job, country, collection)

                            task_manager.run()

                            task.initiate()
                            logger.debug("Task %s is starting (%s: %s)", task, country, collection)

                            break
                        case Task.Status.WAITING | Task.Status.RUNNING:
                            status = task_manager.get_status()
                            logger.debug("Task %s is %s (%s: %s)", task, status, country, collection)

                            match status:
                                case Task.Status.WAITING | Task.Status.RUNNING:
                                    task.progress()  # The service is responding (again). Reset any progress.

                                    break
                                case Task.Status.COMPLETED:
                                    task.complete(result=Task.Result.OK)

                                    # Do not break! Go onto the next task.
                except RecoverableException as e:
                    logger.exception("Recoverable exception during task %s (%s: %s)", task, country, collection)
                    task.progress(result=Task.Result.FAILED, note=str(e))  # The service is not responding.

                    break
                except Exception as e:
                    logger.exception("Unhandled exception during task %s (%s: %s)", task, country, collection)
                    task.complete(result=Task.Result.FAILED, note=str(e))

                    job.complete()
                    logger.warning("Job %s has failed (%s: %s)", job, country, collection)

                    break
            # All tasks completed successfully.
            else:
                job.complete()

                collection.last_retrieved = job.task.get(type=settings.JOB_TASKS_PLAN[0]).end
                collection.save()

                collection.job.update(
                    active=Case(When(id=job.id, then=True), default=False, output_field=BooleanField())
                )

                logger.debug("Job %s has completed (%s: %s)", job, country, collection)


def should_be_planned(collection):
    # frozen collections shouldn't be planned
    if collection.frozen:
        return False

    if not collection.job.exclude(status=Job.Status.COMPLETED):
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
