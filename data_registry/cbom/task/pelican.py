import logging
from urllib.parse import urljoin

from django.conf import settings

from data_registry.cbom.task.exceptions import RecoverableException
from data_registry.cbom.task.task import BaseTask
from data_registry.cbom.utils import request
from data_registry.models import Task

logger = logging.getLogger(__name__)


class Pelican(BaseTask):
    job = None
    collection_id = None

    def __init__(self, job):
        self.job = job
        self.collection_id = self.job.context.get("process_id_pelican")

    def run(self):
        name = self.get_pelican_dataset_name()

        request(
            "POST",
            urljoin(settings.PELICAN_FRONTEND_URL, "/datasets/"),
            json={"name": name, "collection_id": self.collection_id},
            error_msg=f"Publication {self.job.collection}: Pelican: Unable to create dataset with name {name!r} and "
            f"collection ID {self.collection_id}",
        )

    def get_status(self):
        pelican_id = self.get_pelican_id()
        if not pelican_id:
            return Task.Status.WAITING

        resp = request(
            "GET",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/datasets/{pelican_id}/status/"),
            error_msg=f"Publication {self.job.collection}: Pelican: Unable get status of dataset {pelican_id}",
        )

        json = resp.json()
        if not json:
            return Task.Status.WAITING
        if json["phase"] == "CHECKED" and json["state"] == "OK":
            return Task.Status.COMPLETED
        return Task.Status.RUNNING

    def get_pelican_id(self):
        pelican_id = self.job.context.get("pelican_id", None)
        if not pelican_id:
            name = self.get_pelican_dataset_name()

            resp = request(
                "GET",
                urljoin(settings.PELICAN_FRONTEND_URL, "/datasets/find_by_name/"),
                params={"name": name},
                error_msg=f"Publication {self.job.collection}: Pelican: Unable to get ID for name {name!r}",
            )

            pelican_id = resp.json().get("id", None)
            if pelican_id:
                self.job.context["pelican_id"] = pelican_id
                self.job.save()

        return pelican_id

    def get_pelican_dataset_name(self):
        dataset_name = self.job.context.get("pelican_dataset_name", None)
        if not dataset_name:
            spider = self.job.context.get("spider")
            process_data_version = self.job.context.get("process_data_version")

            dataset_name = f"{spider}_{process_data_version}_{self.job.id}"

            self.job.context["pelican_dataset_name"] = dataset_name
            self.job.save()

        return dataset_name

    def wipe(self):
        logger.info("Wiping Pelican data for {}.".format(self.collection_id))
        try:
            pelican_id = self.get_pelican_id()
        except RecoverableException:
            logger.warning("Unable to wipe PELICAN - pelican_id is not set")
            return

        if not pelican_id:
            logger.warning("Unable to wipe PELICAN - pelican_id is not set")
            return

        request(
            "DELETE",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/datasets/{pelican_id}/"),
            error_msg=f"Publication {self.job.collection}: Pelican: Unable to wipe dataset with ID {pelican_id}",
            consume_exception=True,
        )
