import logging
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField, Case, When
from django.utils import timezone

from data_registry.exceptions import RecoverableException
from data_registry.models import Collection, Job, Task
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process
from data_registry.process_manager.util import request

logger = logging.getLogger(__name__)


def get_runner(job, task):
    """
    Task classes must implement three methods:

    -  ``run()`` starts the task
    -  ``get_status()`` returns a choice from ``Task.Status``
    -  ``wipe()`` deletes any side-effects of ``run()``
    """

    match task.type:
        case Task.Type.COLLECT:
            return Collect(job.collection, job)
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
                    if task.status in [Task.Status.WAITING, Task.Status.RUNNING]:
                        status = runner.get_status()
                        logger.debug("Task %s is %s (%s: %s)", task, status, collection.country, collection)
                        if status in [Task.Status.WAITING, Task.Status.RUNNING]:
                            # Reset the task, in case it has recovered.
                            job_complete = False
                            task.result = ""
                            task.note = ""
                            task.save()
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

                            logger.debug("Job %s is starting (%s: %s)", job, collection.country, collection)

                        runner.run()

                        task.start = timezone.now()
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
                    task.end = timezone.now()
                    task.status = Task.Status.COMPLETED
                    task.result = Task.Result.FAILED
                    task.note = str(e)
                    task.save()

                    # close job
                    job.status = Job.Status.COMPLETED
                    job.end = timezone.now()
                    job.save()

                    logger.warning("Job %s has failed (%s: %s)", job, collection.country, collection)
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

                    collection.last_retrieved = job.task.get(type__in=("collect", "test")).end
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

    job = collection.job.create(start=timezone.now(), status=Job.Status.PLANNED)

    for order, task_type in enumerate(settings.JOB_TASKS_PLAN, start=1):
        job.task.create(status=Task.Status.PLANNED, type=task_type, order=order)

    logger.debug("New job %s planned", job)


def update_collection_availability(job):
    try:
        pelican_id = job.context.get("pelican_id")
        response = request("GET", urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/coverage/"))
    except Exception as e:
        raise Exception(
            f"Publication {job.collection}: Pelican: Unable to get coverage of dataset {pelican_id}"
        ) from e

    counts = response.json()

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
        response = request("GET", urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/metadata/"))
    except Exception as e:
        raise Exception(
            f"Publication {job.collection}: Pelican: Unable to get metadata of dataset {pelican_id}"
        ) from e

    meta = response.json()

    if meta:
        job.date_from = parse_date(meta.get("published_from"))
        job.date_to = parse_date(meta.get("published_to"))
        job.license = meta.get("data_license") or ""
        job.ocid_prefix = meta.get("ocid_prefix") or ""
        job.save()


def parse_date(datetime_str):
    if not datetime_str:
        return None

    try:
        try:
            return datetime.strptime(datetime_str, "%Y-%m-%d %H.%M.%S").date()
        except ValueError:  # e.g. nigeria_plateau_state
            return datetime.strptime(datetime_str, "%y-%m-%d %H.%M.%S").date()
    except ValueError as e:
        logger.exception(e)
