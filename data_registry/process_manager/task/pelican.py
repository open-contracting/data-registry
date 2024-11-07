import logging
from urllib.parse import urljoin

from django.conf import settings

from data_registry.models import Task
from data_registry.process_manager.util import TaskManager, skip_if_not_started

logger = logging.getLogger(__name__)


def pelican_url(path):
    return urljoin(settings.PELICAN_FRONTEND_URL, path)


class Pelican(TaskManager):
    final_output = False

    def run(self):
        spider = self.job.context["spider"]  # set in Collect.run()
        data_version = self.job.context["data_version"]  # set in Collect.get_status()
        compiled_collection_id = self.job.context["process_id_pelican"]  # set in Process.get_status()

        name = f"{spider}_{data_version}_{self.job.pk}"

        self.request(
            "POST",
            pelican_url("/api/datasets/"),
            json={
                "name": name,
                "collection_id": compiled_collection_id,
            },
            error_message=f"Unable to create dataset with name {name!r} and collection ID {compiled_collection_id}",
        )

        self.job.context["pelican_dataset_name"] = name
        self.job.save(update_fields=["modified", "context"])

    def get_status(self):
        pelican_id = self.job.context.get("pelican_id")

        if not pelican_id:
            pelican_id = self.get_pelican_id()
            if not pelican_id:
                return Task.Status.WAITING

            self.job.context["pelican_id"] = pelican_id
            self.job.save(update_fields=["modified", "context"])

        response = self.request(
            "GET",
            pelican_url(f"/api/datasets/{pelican_id}/status/"),
            error_message=f"Unable to get status of dataset {pelican_id}",
        )

        data = response.json()

        if not data:
            return Task.Status.WAITING
        if data["phase"] != "CHECKED" or data["state"] != "OK":
            return Task.Status.RUNNING

        response = self.request(
            "GET",
            pelican_url(f"/api/datasets/{pelican_id}/coverage/"),
            error_message=f"Unable to get coverage of dataset {pelican_id}",
        )

        counts = response.json()

        mapping = {
            "tenders_count": "tenders",
            "tenderers_count": "tenderers",
            "tenders_items_count": "tenders_items",
            "parties_count": "parties",
            "awards_count": "awards",
            "awards_items_count": "awards_items",
            "awards_suppliers_count": "awards_suppliers",
            "contracts_count": "contracts",
            "contracts_items_count": "contracts_items",
            "contracts_transactions_count": "contracts_transactions",
            "documents_count": "documents",
            "plannings_count": "plannings",
            "milestones_count": "milestones",
            "amendments_count": "amendments",
        }
        for key, value in mapping.items():
            setattr(self.job, key, counts.get(value))
        self.job.save(update_fields=["modified", *mapping])

        return Task.Status.COMPLETED

    def get_pelican_id(self):
        name = self.job.context["pelican_dataset_name"]  # set in run()

        response = self.request(
            "GET",
            pelican_url("/api/datasets/find_by_name/"),
            params={"name": name},
            error_message=f"Unable to get ID for name {name!r}",
        )

        data = response.json()

        return data.get("id")

    @skip_if_not_started
    def wipe(self):
        pelican_id = self.job.context.get("pelican_id")  # set in get_status()

        # `pelican_id` can be missing because:
        #
        # - The Pelican API stopped responding after run()
        # - The Pelican worker hasn't processed the message yet
        # - wipe() was called before get_status()
        #
        # These temporary errors are too rare to bother with.
        if not pelican_id:
            pelican_id = self.get_pelican_id()
            if not pelican_id:
                logger.warning("%s: Unable to wipe dataset (dataset ID is not set)", self)
                return

        logger.info("%s: Wiping data for dataset %s", self, pelican_id)
        self.request(
            "DELETE",
            pelican_url(f"/api/datasets/{pelican_id}/"),
            error_message=f"Unable to wipe dataset {pelican_id}",
        )
