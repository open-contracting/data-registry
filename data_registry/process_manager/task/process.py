import logging
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings

from data_registry.exceptions import IrrecoverableError
from data_registry.models import Task
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


def url_for_collection(*parts):
    return urljoin(settings.KINGFISHER_PROCESS_URL, f"/api/collections/{'/'.join(map(str, parts))}/")


def parse_date(dt):
    if dt:
        # 2023-10-27T17:14:07:00Z nigeria_ebonyi_state
        #                    ^^^
        if dt.endswith("Z") and dt.count(":") == 3:
            dt = ".".join(dt.rsplit(":", 1))

        # 2024-05-01 16:30:04.160T12:00:00Z italy_anac
        #                        ^^^^^^^^^
        if " " in dt and "T12:00:00" in dt:
            dt = dt.replace("T12:00:00", "").replace(" ", "T")

        if len(dt) == 10:
            return datetime.strptime(dt, "%Y-%m-%d").date()
        if "." in dt:
            return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f%z").date()
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S%z").date()
    return dt


class Process(TaskManager):
    final_output = False

    def run(self):
        # Kingfisher Process is started by Kingfisher Collect's Kingfisher Process API extension.
        pass

    def get_status(self):
        process_id = self.job.context["process_id"]  # set in Collect.get_status()

        tree = self.request(
            "GET",
            url_for_collection(process_id, "tree"),
            error_message=f"Unable to get status of collection {process_id}",
        ).json()

        original_collection = next(c for c in tree if c["transform_type"] == "")
        compiled_collection = next(c for c in tree if c["transform_type"] == "compile-releases")

        if not original_collection["completed_at"] or not compiled_collection["completed_at"]:
            return Task.Status.RUNNING

        meta = self.request(
            "GET",
            url_for_collection(compiled_collection["id"], "metadata"),
            error_message=f"Unable to get metadata of collection {compiled_collection['id']}",
        ).json()

        # The metadata can be empty (or partial) if the collection contained no data.
        if meta:
            self.job.date_from = parse_date(meta.get("published_from"))
            self.job.date_to = parse_date(meta.get("published_to"))
            self.job.license = meta.get("license") or ""
            self.job.publication_policy = meta.get("publication_policy") or ""
            self.job.ocid_prefix = meta.get("ocid_prefix") or ""

        self.job.context["process_compiled_collection_id"] = compiled_collection["id"]

        self.job.process_notes = self.request(
            "GET",
            url_for_collection(original_collection["id"], "notes"),
            params=[("level", "WARNING"), ("level", "ERROR")],
            error_message=f"Unable to get notes of collection {original_collection['id']}",
        ).json()

        self.job.save(
            update_fields=[
                "modified",
                "context",
                "date_from",
                "date_to",
                "license",
                "publication_policy",
                "ocid_prefix",
                "process_notes",
            ]
        )

        if original_collection["expected_files_count"] == 0:
            raise IrrecoverableError("Collection is empty")

        return Task.Status.COMPLETED

    # Don't use @skip_if_not_started, because Kingfisher Process can start before the Process task starts.
    def wipe(self):
        # `process_id` can be missing for the reasons in Collect.wipe().
        if "process_id" not in self.job.context:
            logger.warning("%s: Unable to wipe collection (collection ID is not set)", self)
            return

        process_id = self.job.context["process_id"]  # set in Collect.get_status()

        logger.info("%s: Wiping data for collection %s", self, process_id)
        self.request(
            "DELETE",
            url_for_collection(process_id),
            error_message=f"Unable to wipe collection {process_id}",
        )
