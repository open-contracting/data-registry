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
        self.compiled_collection_id = self.job.context.get("process_id_pelican")

    def run(self):
        name = self.get_pelican_dataset_name()

        self.request(
            "POST",
            urljoin(settings.PELICAN_FRONTEND_URL, "/api/datasets/"),
            json={"name": name, "collection_id": self.compiled_collection_id},
            error_msg=f"Unable to create dataset with name {name!r} and collection ID {self.compiled_collection_id}",
        )

    def get_status(self):
        pelican_id = self.get_pelican_id()
        if not pelican_id:
            return Task.Status.WAITING

        response = self.request(
            "GET",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/status/"),
            error_msg=f"Unable to get status of dataset {pelican_id}",
        )

        data = response.json()

        if not data:
            return Task.Status.WAITING
        if data["phase"] == "CHECKED" and data["state"] == "OK":
            return Task.Status.COMPLETED
        return Task.Status.RUNNING

    def get_pelican_id(self):
        if "pelican_id" not in self.job.context:
            name = self.get_pelican_dataset_name()

            response = self.request(
                "GET",
                urljoin(settings.PELICAN_FRONTEND_URL, "/api/datasets/find_by_name/"),
                params={"name": name},
                error_msg=f"Unable to get ID for name {name!r}",
            )

            data = response.json()

            if "id" in data:
                self.job.context["pelican_id"] = data["id"]
                self.job.save()

        return self.job.context.get("pelican_id")

    def get_pelican_dataset_name(self):
        if "pelican_dataset_name" not in self.job.context:
            spider = self.job.context["spider"]
            process_data_version = self.job.context["process_data_version"]
            self.job.context["pelican_dataset_name"] = f"{spider}_{process_data_version}_{self.job.id}"
            self.job.save()

        return self.job.context["pelican_dataset_name"]

    def wipe(self):
        try:
            pelican_id = self.get_pelican_id()
        except RecoverableException:
            logger.error("%s: Unable to wipe dataset (dataset ID is irretrievable)", self)
            return

        if not pelican_id:
            logger.warning("%s: Unable to wipe dataset (dataset ID is empty)", self)
            return

        logger.info("%s: Wiping data for collection %s", self, self.compiled_collection_id)
        self.request(
            "DELETE",
            urljoin(settings.PELICAN_FRONTEND_URL, f"/api/datasets/{pelican_id}/"),
            error_msg=f"Unable to wipe dataset {pelican_id}",
            consume_exception=True,
        )
