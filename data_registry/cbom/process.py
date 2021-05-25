import logging

from django.conf import settings
from django.db import transaction
from django.db.models.expressions import Case, When
from django.db.models.fields import BooleanField
from django.db.models.query_utils import Q
from django.utils import timezone

from data_registry.cbom.task.exceptions import RecoverableException
from data_registry.cbom.task.factory import TaskFactory
from data_registry.cbom.utils import request
from data_registry.models import Job, Task

logger = logging.getLogger('cbom')


def process(collection):
    logger.debug(f"Processing collection {collection}")

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
            job_complete = True

            for task in tasks:
                # finished task -> no action needed
                if task.status == Task.Status.COMPLETED:
                    continue

                _task = TaskFactory.get_task(collection, job, task)

                try:
                    if task.status in [Task.Status.WAITING, Task.Status.RUNNING]:
                        status = _task.get_status()
                        logger.debug(f"Task {task} {status}")
                        if status in [Task.Status.WAITING, Task.Status.RUNNING]:
                            # do nothing, the task is still running
                            job_complete = False
                            break
                        elif status == Task.Status.COMPLETED:
                            # complete the task
                            task.end = timezone.now()
                            task.status = Task.Status.COMPLETED
                            task.result = Task.Result.OK

                            task.save()
                    elif task.status == Task.Status.PLANNED:
                        if job.status == Job.Status.PLANNED:
                            job.start = timezone.now()
                            job.status = Job.Status.RUNNING
                            job.save()

                            logger.debug(f"Job {job} started")

                        # run the task
                        _task.run()
                        task.start = timezone.now()
                        task.status = Task.Status.RUNNING
                        job_complete = False

                        logger.debug(f"Task {task} started")

                        task.save()

                        break
                except RecoverableException as e:
                    job_complete = False
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    logger.exception(e)
                    break
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
                # completed job postprocessing
                try:
                    # get dataset availability
                    pelican_id = job.context.get("pelican_id")
                    resp = request(
                        "GET",
                        f"{settings.PELICAN_HOST}api/dataset_availability/{pelican_id}"
                    )

                    counts = resp.json().get("data")

                    job.collection.tenders_count = counts.get("tenders")
                    job.collection.tenderers_count = counts.get("tenderers")
                    job.collection.tenders_items_count = counts.get("tenders_items")
                    job.collection.parties_count = counts.get("parties")
                    job.collection.awards_count = counts.get("awards")
                    job.collection.awards_items_count = counts.get("awards_items")
                    job.collection.awards_suppliers_count = counts.get("awards_suppliers")
                    job.collection.contracts_count = counts.get("contracts")
                    job.collection.contracts_items_count = counts.get("contracts_items")
                    job.collection.contracts_transactions_count = counts.get("contracts_transactions")
                    job.collection.documents_count = counts.get("documents")
                    job.collection.plannings_count = counts.get("plannings")
                    job.collection.milestones_count = counts.get("milestones")
                    job.collection.amendments_count = counts.get("amendments")
                    job.collection.save()
                except Exception:
                    logger.exception("Unable get dataset availability from pelican")
                else:
                    job.status = Job.Status.COMPLETED
                    job.end = timezone.now()
                    job.save()

                    # set active job
                    Job.objects\
                        .filter(collection=job.collection)\
                        .update(active=Case(
                            When(id=job.id, then=True),
                            default=False,
                            output_field=BooleanField()
                        ))

                    logger.debug(f"Job {job} completed")


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

    logger.debug(f"New job {job} planned")
