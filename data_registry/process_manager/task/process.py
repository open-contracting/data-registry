import logging
from urllib.parse import urljoin

from django.conf import settings

from data_registry.models import Task
from data_registry.process_manager.util import request

logger = logging.getLogger(__name__)


def _url(path):
    return urljoin(settings.KINGFISHER_PROCESS_URL, f"/api/collections/{path}/")


class Process:
    def __init__(self, job):
        self.job = job
        self.process_id = job.context.get("process_id")

    def run(self):
        # process is started through collect-process integration
        pass

    def get_status(self):
        response = request(
            "GET",
            _url(f"{self.process_id}/tree"),
            error_msg=f"Unable to get status of process #{self.process_id}",
        )

        json = response.json()

        compile_releases = next(n for n in json if n.get("transform_type") == "compile-releases")
        is_last_completed = compile_releases.get("completed_at") is not None

        if "process_id_pelican" not in self.job.context:
            self.job.context["process_id_pelican"] = compile_releases.get("id")
            self.job.context["process_data_version"] = compile_releases.get("data_version")
            self.job.save()

        if is_last_completed:
            response = request(
                "GET",
                _url(f"{compile_releases.get('id')}/metadata"),
                error_msg=f"Unable to get the metadata of process #{compile_releases.get('id')}",
            )
            meta = response.json()
            if meta:
                self.job.date_from = meta.get("published_from")
                self.job.date_to = meta.get("published_to")
                self.job.license = meta.get("data_license") or ""
                self.job.ocid_prefix = meta.get("ocid_prefix") or ""
                self.job.save()

        return Task.Status.COMPLETED if is_last_completed else Task.Status.RUNNING

    def wipe(self):
        if not self.process_id:
            logger.warning("Unable to wipe PROCESS - process_id is not set (because log file was not retrievable)")
            return

        logger.info("Wiping Kingfisher Process data for collection id %s.", self.process_id)
        request(
            "DELETE",
            _url(self.process_id),
            error_msg="Unable to wipe PROCESS",
        )
