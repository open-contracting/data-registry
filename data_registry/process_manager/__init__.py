import logging

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Case, When

from data_registry.exceptions import RecoverableException
from data_registry.models import Job, Task
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
    """
    If the collection is :meth:`out-of-date<data_registry.models.Collection.is_out_of_date>`, create a job.

    For each of the collection's incomplete jobs:

    -  If the job is planned, start the job
    -  If the next task is planned, start the task
    -  If the next task is waiting or running, recheck its status:

       -  If it is completed, complete the task and start the next task
       -  If it failed temporarily, log the reason
       -  If it failed permanently, fail the task and end the job

    -  If all tasks succeeded, end the job and update the collection's active job and last retrieved date.

    As such, for all tasks of a job to succeed, this function needs to run at least as many times are there are tasks
    in the ``JOB_TASKS_PLAN`` setting.
    """
    if collection.is_out_of_date():
        collection.job_set.create()  # see signals.py

    country = collection.country

    for job in collection.job_set.incomplete():
        with transaction.atomic():
            for task in job.task_set.exclude(status=Task.Status.COMPLETED).order_by("order"):
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

                collection.last_retrieved = job.task_set.get(type=settings.JOB_TASKS_PLAN[0]).end
                collection.save()

                collection.job_set.update(
                    active=Case(When(id=job.id, then=True), default=False, output_field=BooleanField())
                )

                logger.debug("Job %s has succeeded (%s: %s)", job, country, collection)
