import logging

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Case, When

from data_registry import models
from data_registry.exceptions import RecoverableException
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


def get_task_manager(task: models.Task) -> TaskManager:
    """
    Instantiate and return a task manager for the task.
    """
    match task.type:
        case models.Task.Type.COLLECT:
            return Collect(task)
        case models.Task.Type.PROCESS:
            return Process(task)
        case models.Task.Type.PELICAN:
            return Pelican(task)
        case models.Task.Type.EXPORTER:
            return Exporter(task)
        case models.Task.Type.FLATTENER:
            return Flattener(task)
        case _:
            raise Exception("Unsupported task type")


def process(collection: models.Collection) -> None:
    """
    If the collection is :meth:`out-of-date<data_registry.models.Collection.is_out_of_date>`, create a job.

    For each of the collection's incomplete jobs:

    -  If the job is planned, start the job
    -  If the next task is planned, start the task with :meth:`~data_registry.process_manager.util.TaskManager.run`
    -  If the next task is waiting or running, recheck its status with
       :meth:`~data_registry.process_manager.util.TaskManager.get_status`:

       -  If it is completed, complete the task and start the next task
       -  If it failed temporarily, log the reason
       -  If it failed permanently, fail the task and end the job

    -  If all tasks succeeded, end the job and update the collection's active job and last retrieved date.

    In other words, this function advances each job by at most one task. As such, for all tasks of a job to succeed,
    this function needs to run at least as many times are there are tasks in the ``JOB_TASKS_PLAN`` setting.
    """
    if collection.is_out_of_date():
        collection.job_set.create()  # see signals.py

    country = collection.country

    for job in collection.job_set.incomplete():
        with transaction.atomic():
            for task in job.task_set.exclude(status=models.Task.Status.COMPLETED).order_by("order"):
                task_manager = get_task_manager(task)

                try:
                    match task.status:
                        case models.Task.Status.PLANNED:
                            # If this is the first task...
                            if job.status == models.Job.Status.PLANNED:
                                job.initiate()
                                logger.debug("Job %s is starting (%s: %s)", job, country, collection)

                            task_manager.run()

                            task.initiate()
                            logger.debug("Task %s is starting (%s: %s)", task, country, collection)

                            break
                        case models.Task.Status.WAITING | models.Task.Status.RUNNING:
                            status = task_manager.get_status()
                            logger.debug("Task %s is %s (%s: %s)", task, status, country, collection)

                            match status:
                                case models.Task.Status.WAITING | models.Task.Status.RUNNING:
                                    task.progress()  # The application is responding (again). Reset any progress.

                                    break
                                case models.Task.Status.COMPLETED:
                                    task.complete(result=models.Task.Result.OK)

                                    # Do not break! Go onto the next task.
                except RecoverableException as e:
                    logger.exception("Recoverable exception during task %s (%s: %s)", task, country, collection)
                    task.progress(result=models.Task.Result.FAILED, note=str(e))  # The application is not responding.

                    break
                except Exception as e:
                    logger.exception("Unhandled exception during task %s (%s: %s)", task, country, collection)
                    task.complete(result=models.Task.Result.FAILED, note=str(e))

                    job.complete()
                    logger.warning("Job %s has failed (%s: %s)", job, country, collection)

                    break
            # All tasks completed successfully.
            else:
                job.complete()

                collection.last_retrieved = job.task_set.get(type=settings.JOB_TASKS_PLAN[0]).end
                collection.save()

                collection.job_set.update(
                    active=Case(When(id=job.id, then=True), default=False, output_field=BooleanField())
                )

                logger.debug("Job %s has succeeded (%s: %s)", job, country, collection)
