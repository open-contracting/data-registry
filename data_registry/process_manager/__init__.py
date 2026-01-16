import datetime
import logging

from django.conf import settings
from django.db import transaction
from django.utils.timezone import now

from data_registry import models
from data_registry.exceptions import RecoverableError
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.coverage import Coverage
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.process import Process
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)

FLATTENER_EXECUTION_LIMIT = datetime.timedelta(days=1)
UNSUCCESSFUL_JOB_RETENTION = datetime.timedelta(days=180)


def get_task_manager(task: models.Task) -> TaskManager:
    """Instantiate and return a task manager for the task."""
    match task.type:
        case models.Task.Type.COLLECT:
            return Collect(task)
        case models.Task.Type.PROCESS:
            return Process(task)
        case models.Task.Type.EXPORTER:
            return Exporter(task)
        case models.Task.Type.COVERAGE:
            return Coverage(task)
        case models.Task.Type.FLATTENER:
            return Flattener(task)
        case _:
            raise NotImplementedError(repr(task.type))


def delete_older_jobs(collection: models.Collection, job: models.Job, *, dry_run: bool = False) -> None:
    """
    Delete old jobs for a collection.

    - Delete past unsuccessful jobs older than 180 days
    - Delete past successful jobs with less than 10% more OCIDs, keeping the second-most recent job

    :param collection: The collection on which to operate
    :param job: A job to keep and to which to compare OCID counts
    :param dry_run: Show what would be done, without making changes
    """
    country = collection.country

    other_jobs = collection.job_set.exclude(pk=job.pk)
    # Keep the second-most recent successful job.
    old_successful_jobs = other_jobs.successful().order_by("-start")[1:]
    # Keep unsuccessful jobs for six months, for debugging.
    old_unsuccessful_jobs = other_jobs.unsuccessful().filter(start__lt=now() - UNSUCCESSFUL_JOB_RETENTION)
    # NOTE: Administrators must check incomplete jobs manually.

    # NOTE: The Collect task's wipe() method can be slow.

    for old_job in old_unsuccessful_jobs:
        if dry_run:
            logger.info("DRY RUN: Would delete old unsuccessful job %s (%s: %s)", old_job, country, collection)
        else:
            old_job.delete()
            logger.debug("Deleted old unsuccessful job %s (%s: %s)", old_job, country, collection)

    new_ocid_count = job.coverage.get("/ocid", 0)
    for old_job in old_successful_jobs:
        old_ocid_count = old_job.coverage.get("/ocid", 0)
        if old_ocid_count <= new_ocid_count * 1.1:
            if dry_run:
                logger.info("DRY RUN: Would delete old successful job %s (%s: %s)", old_job, country, collection)
            else:
                old_job.delete()
                logger.debug("Deleted old successful job %s (%s: %s)", old_job, country, collection)
        else:
            logger.warning(
                "Keeping old job %s with over 10%% more OCIDs than newest job %s (%s >> %s) (%s: %s)",
                old_job,
                job,
                old_ocid_count,
                new_ocid_count,
                country,
                collection,
            )


def process(collection: models.Collection, *, dry_run: bool = False) -> None:
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
       - Delete past unsuccessful jobs older than 180 days
       - Delete past successful jobs with less than 10% more OCIDs, keeping the active and next-most recent job

    In other words, this function advances each job by at most one task. As such, for all tasks of a job to succeed,
    this function needs to run at least as many times are there are tasks in the ``JOB_TASKS_PLAN`` setting.

    :param collection: The collection to process
    :param dry_run: Show what would be done, without making changes
    """
    country = collection.country

    if collection.is_out_of_date():
        if dry_run:
            logger.info("DRY RUN: Would create job for out-of-date collection %s: %s", country, collection)
        else:
            collection.job_set.create()  # see signals.py

    for job in collection.job_set.incomplete():
        for task in job.task_set.exclude(status=models.Task.Status.COMPLETED).order_by("order"):
            task_manager = get_task_manager(task)

            if dry_run:
                logger.info("DRY RUN: Would progress task %s for job %s (%s: %s)", task, job, country, collection)
                continue

            try:
                with transaction.atomic():
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
                            status, note = task_manager.get_status()
                            logger.debug("Task %s is %s (%s: %s)", task, status, country, collection)

                            match status:
                                case models.Task.Status.WAITING | models.Task.Status.RUNNING:
                                    task.progress()  # The application is responding (again). Reset any progress.

                                    # Check if the flattener task has been stuck for a day.
                                    if (
                                        task.type == models.Task.Type.FLATTENER
                                        and now() - task.start > FLATTENER_EXECUTION_LIMIT
                                    ):
                                        # Perform the same actions as the PLANNED branch.
                                        task_manager.run()

                                        task.initiate()
                                        logger.warning("Task %s is restarting (%s: %s)", task, country, collection)

                                    break
                                case models.Task.Status.COMPLETED:
                                    if note:
                                        logger.warning("Task %s failed (%s: %s): %s", task, country, collection, note)
                                        task.complete(result=models.Task.Result.FAILED, note=note)

                                        job.complete()
                                        logger.warning("Job %s has failed (%s: %s)", job, country, collection)

                                        break

                                    task.complete(result=models.Task.Result.OK)

                                    # Do not break! Go onto the next task.
            except RecoverableError as e:
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
            if dry_run:
                logger.info("DRY RUN: Would complete job %s and update collection %s: %s", job, country, collection)
            else:
                with transaction.atomic():
                    job.complete()

                    collection.last_retrieved = job.task_set.get(type=settings.JOB_TASKS_PLAN[0]).end
                    collection.active_job = job
                    if not collection.publication_policy:
                        collection.publication_policy = job.publication_policy
                    collection.save()

            logger.debug("Job %s has succeeded (%s: %s)", job, country, collection)

            delete_older_jobs(collection, job, dry_run=dry_run)
