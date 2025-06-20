import datetime
import logging

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from data_registry import models
from data_registry.exceptions import IrrecoverableError, RecoverableError
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.process import Process
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


def get_task_manager(task: models.Task) -> TaskManager:
    """Instantiate and return a task manager for the task."""
    match task.type:
        case models.Task.Type.COLLECT:
            return Collect(task)
        case models.Task.Type.PROCESS:
            return Process(task)
        case models.Task.Type.EXPORTER:
            return Exporter(task)
        case models.Task.Type.FLATTENER:
            return Flattener(task)
        case _:
            raise NotImplementedError(repr(task.type))


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

    -  If all tasks succeeded:

       - End the job
       - Update the collection's active job and last retrieved date
       - Delete jobs that are more than a year older than the active job, but keep one other complete job

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
                except RecoverableError as e:
                    logger.exception("Recoverable exception during task %s (%s: %s)", task, country, collection)
                    task.progress(result=models.Task.Result.FAILED, note=str(e))  # The application is not responding.

                    break
                except IrrecoverableError as e:
                    logger.warning("Irrecoverable error during task %s (%s: %s): %s", task, country, collection, e)
                    task.complete(result=models.Task.Result.FAILED, note=str(e))

                    job.complete()
                    logger.warning("Job %s has failed (%s: %s)", job, country, collection)

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
                collection.active_job = job
                if not collection.publication_policy:
                    collection.publication_policy = job.publication_policy
                collection.save()

                logger.debug("Job %s has succeeded (%s: %s)", job, country, collection)

                # Keep the other most recent successful job as backup.
                other_jobs = collection.job_set.exclude(pk=job.pk)
                backup_job = other_jobs.successful().order_by("start").values_list("pk", flat=True).last()
                if backup_job:
                    other_jobs = other_jobs.exclude(pk=backup_job)

                # There must be at most one incomplete job per collection, for deletion to not conflict with iteration.
                for old_job in other_jobs.filter(start__lt=now() - datetime.timedelta(days=365)):
                    # Note: The Collect task's wipe() method can be slow.
                    old_job.delete()
                    logger.debug("Old job %s has been deleted (%s: %s)", old_job, country, collection)
