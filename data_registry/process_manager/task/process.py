import logging
from urllib.parse import urljoin

from django.conf import settings

from data_registry.models import Task
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


def url_for_collection(*parts):
    return urljoin(settings.KINGFISHER_PROCESS_URL, f"/api/collections/{'/'.join(map(str, parts))}/")


class Process(TaskManager):
    @property
    def final_output(self):
        return False

    def run(self):
        # The Process task is started by Kingfisher Collect's Kingfisher Process API extension.
        pass

    def get_status(self):
        process_id = self.job.context["process_id"]  # set in Collect.get_status()

        response = self.request(
            "GET",
            url_for_collection(process_id, "tree"),
            error_message=f"Unable to get status of collection #{process_id}",
        )

        tree = response.json()

        compiled_collection = next(c for c in tree if c["transform_type"] == "compile-releases")

        if not compiled_collection["completed_at"]:
            return Task.Status.RUNNING

        response = self.request(
            "GET",
            url_for_collection(compiled_collection["id"], "metadata"),
            error_message=f"Unable to get metadata of collection #{compiled_collection['id']}",
        )

        meta = response.json()

        # The metadata can be empty (or partial) if the collection contained no data.
        if meta:
            self.job.date_from = meta.get("published_from")
            self.job.date_to = meta.get("published_to")
            self.job.license = meta.get("data_license") or ""
            self.job.ocid_prefix = meta.get("ocid_prefix") or ""

        self.job.context["process_id_pelican"] = compiled_collection["id"]
        self.job.save()

        return Task.Status.COMPLETED

    def do_wipe(self):
        process_id = self.job.context["process_id"]  # set in Collect.get_status()

        logger.info("%s: Wiping data for collection %s", self, process_id)
        self.request(
            "DELETE",
            url_for_collection(process_id),
            error_message=f"Unable to wipe collection {process_id}",
        )
