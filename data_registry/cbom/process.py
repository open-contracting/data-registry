import logging
from datetime import date, datetime, timedelta

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

logger = logging.getLogger(__name__)


def process(collection):
    logger.debug(f"Processing collection {collection.country} - {collection}")

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
                        task.save()

                        job_complete = False

                        logger.debug(f"Task {task} started")

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
                    task.end = timezone.now()
                    task.status = Task.Status.COMPLETED
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    # close job
                    job.status = Job.Status.COMPLETED
                    job.end = timezone.now()
                    job.save()

                    logger.debug(f"Job {job} failed")
                    break

            # complete the job if all of its tasks are completed
            if job_complete:
                # completed job postprocessing
                try:
                    update_collection_availability(job)

                    update_collection_metadata(job)
                except Exception as e:
                    logger.exception(e)
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
        # update frequency is not set, plan next job
        if not collection.update_frequency:
            return True

        # plan next job depending on update frequency
        last_job = Job.objects.filter(collection=collection, status=Job.Status.COMPLETED).order_by("-start").first()
        if not last_job:
            return True

        delta = timedelta(days=30)  # MONTHLY
        if collection.update_frequency == "HALF_YEARLY":
            delta = timedelta(days=180)
        elif collection.update_frequency == "ANNUALLY":
            delta = timedelta(days=365)

        return date.today() >= (last_job.start + delta).date()
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


def update_collection_availability(job):
    try:
        pelican_id = job.context.get("pelican_id")
        resp = request(
            "GET",
            f"{settings.PELICAN_HOST}datasets/{pelican_id}/coverage/"
        )
    except Exception as e:
        raise Exception(f"Publication {job.collection}: Pelican: Unable to get coverage of dataset {pelican_id}") from e

    counts = resp.json()

    job.tenders_count = counts.get("tenders")
    job.tenderers_count = counts.get("tenderers")
    job.tenders_items_count = counts.get("tenders_items")
    job.parties_count = counts.get("parties")
    job.awards_count = counts.get("awards")
    job.awards_items_count = counts.get("awards_items")
    job.awards_suppliers_count = counts.get("awards_suppliers")
    job.contracts_count = counts.get("contracts")
    job.contracts_items_count = counts.get("contracts_items")
    job.contracts_transactions_count = counts.get("contracts_transactions")
    job.documents_count = counts.get("documents")
    job.plannings_count = counts.get("plannings")
    job.milestones_count = counts.get("milestones")
    job.amendments_count = counts.get("amendments")
    job.save()


def update_collection_metadata(job):
    try:
        pelican_id = job.context.get("pelican_id")
        resp = request(
            "GET",
            f"{settings.PELICAN_HOST}datasets/{pelican_id}/metadata/"
        )
    except Exception as e:
        raise Exception(f"Publication {job.collection}: Pelican: Unable to get metadata of dataset {pelican_id}") from e

    meta = resp.json()

    if meta:
        job.date_from = parse_date(meta.get("published_from"))
        job.date_to = parse_date(meta.get("published_to"))
        job.license = meta.get("data_license")
        job.ocid_prefix = meta.get("ocid_prefix")
        job.save()


def parse_date(datetime_str):
    if not datetime_str:
        return None

    datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d %H.%M.%S')
    return datetime_obj.date()
