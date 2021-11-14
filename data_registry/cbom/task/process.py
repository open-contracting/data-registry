import logging

from django.conf import settings

from data_registry.cbom.task.task import BaseTask
from data_registry.cbom.utils import request
from data_registry.models import Task

logger = logging.getLogger(__name__)


class Process(BaseTask):
    job = None
    process_id = None

    def __init__(self, job):
        self.job = job
        self.process_id = job.context.get("process_id", None)

    def run(self):
        # process is started throught scrape-process integration
        pass

    def get_status(self):
        resp = request(
            "GET",
            f"{settings.KINGFISHER_PROCESS_HOST}api/v1/tree/{self.process_id}/",
            error_msg=f"Unable to get status of process #{self.process_id}",
        )

        json = resp.json()

        compile_releases = next(n for n in json if n.get("transform_type", None) == "compile-releases")
        is_last_completed = compile_releases.get("completed_at", None) is not None

        if "process_id_pelican" not in self.job.context:
            self.job.context["process_id_pelican"] = compile_releases.get("id")
            self.job.context["process_data_version"] = compile_releases.get("data_version")
            self.job.save()

        return Task.Status.COMPLETED if is_last_completed else Task.Status.RUNNING

    def wipe(self):
        logger.info("Wiping process data for {}.".format(self.process_id))
        request(
            "POST",
            f"{settings.KINGFISHER_PROCESS_HOST}api/v1/wipe_collection",
            json={"collection_id": self.process_id},
            error_msg="Unable to wipe PROCESS",
            consume_exception=True,
        )
