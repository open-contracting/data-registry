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
            error_msg=f"Unable to get status of collection #{process_id}",
        )

        tree = response.json()

        compiled_collection = next(c for c in tree if c["transform_type"] == "compile-releases")

        # Write "process_data_version" early, since the Collect task uses it to wipe, even if the Process task fails.
        if "process_data_version" not in self.job.context:
            self.job.context["process_id_pelican"] = compiled_collection["id"]
            self.job.context["process_data_version"] = compiled_collection["data_version"]
            self.job.save()

        if compiled_collection["completed_at"]:
            response = self.request(
                "GET",
                url_for_collection(compiled_collection["id"], "metadata"),
                error_msg=f"Unable to get metadata of collection #{compiled_collection['id']}",
            )

            meta = response.json()

            if meta:  # can be empty (or partial) if the collection contained no data
                self.job.date_from = meta.get("published_from")
                self.job.date_to = meta.get("published_to")
                self.job.license = meta.get("data_license") or ""
                self.job.ocid_prefix = meta.get("ocid_prefix") or ""
                self.job.save()

            return Task.Status.COMPLETED

        return Task.Status.RUNNING

    def wipe(self):
        if "process_id" not in self.job.context:  # for example, if Collect task failed
            logger.warning("%s: Unable to wipe collection (collection ID is not set)", self)
            return

        process_id = self.job.context["process_id"]  # set in Collect.get_status()

        logger.info("%s: Wiping data for collection %s", self, process_id)
        self.request(
            "DELETE",
            url_for_collection(process_id),
            error_msg=f"Unable to wipe collection {process_id}",
        )
