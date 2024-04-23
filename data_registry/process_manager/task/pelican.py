import logging
from urllib.parse import urljoin

from django.conf import settings

from data_registry.exceptions import RecoverableException
from data_registry.models import Task
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


class Pelican(TaskManager):
    def __init__(self, job):
        self.job = job
        self.collection_id = self.job.context.get("process_id_pelican")

    def run(self):
        name = self.get_pelican_dataset_name()

        self.request(
            "POST",
            urljoin(settings.PELICAN_FRONTEND_URL, "/api/datasets/"),
            json={"name": name, "collection_id": self.collection_id},
            error_msg=f"Unable to create dataset with name {name!r} and collection ID {self.collection_id}",
        )

    def get_status(self):
        pelican_id = self.get_pelican_id()
        if not pelican_id:
            return Task.Status.WAITING

        response = self.request(
            "GET",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/status/"),
            error_msg=f"Unable get status of dataset {pelican_id}",
        )

        json = response.json()
        if not json:
            return Task.Status.WAITING
        if json["phase"] == "CHECKED" and json["state"] == "OK":
            return Task.Status.COMPLETED
        return Task.Status.RUNNING

    def get_pelican_id(self):
        pelican_id = self.job.context.get("pelican_id")
        if not pelican_id:
            name = self.get_pelican_dataset_name()

            response = self.request(
                "GET",
                urljoin(settings.PELICAN_FRONTEND_URL, "/api/datasets/find_by_name/"),
                params={"name": name},
                error_msg=f"Unable to get ID for name {name!r}",
            )

            pelican_id = response.json().get("id")
            if pelican_id:
                self.job.context["pelican_id"] = pelican_id
                self.job.save()

        return pelican_id

    def get_pelican_dataset_name(self):
        dataset_name = self.job.context.get("pelican_dataset_name")
        if not dataset_name:
            spider = self.job.context.get("spider")
            process_data_version = self.job.context.get("process_data_version")

            dataset_name = f"{spider}_{process_data_version}_{self.job.id}"

            self.job.context["pelican_dataset_name"] = dataset_name
            self.job.save()

        return dataset_name

    def wipe(self):
        logger.info("Wiping Pelican data for collection id %s.", self.collection_id)
        try:
            pelican_id = self.get_pelican_id()
        except RecoverableException:
            logger.error("Unable to wipe PELICAN - pelican_id is not retrievable")
            return

        if not pelican_id:
            logger.warning("Unable to wipe PELICAN - pelican_id is not set")
            return

        self.request(
            "DELETE",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/"),
            error_msg=f"Unable to wipe dataset with ID {pelican_id}",
            consume_exception=True,
        )
