import logging
import re
from collections import Counter
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings

from data_registry.exceptions import IrrecoverableError
from data_registry.models import Task
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)

OCDS_MERGE_WARNING_PATTERN = re.compile(
    r"^Multiple objects have the `id` value '.+' in the `(.+)` array$", re.MULTILINE
)


def url_for_collection(*parts):
    return urljoin(settings.KINGFISHER_PROCESS_URL, f"/api/collections/{'/'.join(map(str, parts))}/")


def parse_date(dt):
    if dt:
        # 2024-05-01 16:30:04.160T12:00:00Z italy_anac
        #                        ^^^^^^^^^
        if " " in dt and "T12:00:00" in dt:
            dt = dt.replace("T12:00:00", "")
        return datetime.fromisoformat(dt).date()
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
        try:
            compiled_collection = next(c for c in tree if c["transform_type"] == "compile-releases")
        except StopIteration:
            raise IrrecoverableError("No compiled collection") from None

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

        process_notes = self.request(
            "GET",
            url_for_collection(original_collection["id"], "notes"),
            params=[("level", "WARNING"), ("level", "ERROR")],
            error_message=f"Unable to get notes of collection {original_collection['id']}",
        ).json()

        # OCDS Merge has one warning type, which can be issued millions of times.
        counter = Counter()
        warning_notes = []
        for note, data in process_notes["WARNING"]:
            if note.startswith("Multiple objects have the `id` value "):
                counter.update(OCDS_MERGE_WARNING_PATTERN.findall(note))
            else:
                warning_notes.append([note, data])
        for path, count in counter.items():
            warning_notes.append(["OCDS Merge", {"count": count, "path": path}])
        process_notes["WARNING"] = warning_notes

        self.job.process_notes = process_notes

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
