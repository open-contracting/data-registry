from django.conf import settings

from data_registry.cbom.task.task import BaseTask
from data_registry.cbom.task.utils import request
from data_registry.models import Task


class Exporter(BaseTask):
    job = None
    collection_id = None

    def __init__(self, job):
        self.job = job
        self.collection_id = self.job.context.get("process_id_pelican")
        if not self.collection_id:
            raise Exception("Process id is not set")

    def run(self):
        request(
            "POST",
            f"{settings.EXPORTER_HOST}api/exporter_start",
            json={
                "job_id": self.job.id,
                "collection_id": self.collection_id,
                "spider": self.job.context.get("spider")
            },
            error_msg=f"Unable to run Exporter for collection {self.job.collection}"
        )

    def get_status(self):
        resp = request(
            "POST",
            f"{settings.EXPORTER_HOST}api/exporter_status",
            json={
                "job_id": self.job.id,
                "collection_id": self.collection_id,
                "spider": self.job.context.get("spider")
            },
            error_msg=f"Unable get Exporter status for collection {self.job.collection}"
        )

        json = resp.json().get("data")

        if not json or json == "WAITING":
            return Task.Status.WAITING
        elif json == "RUNNING":
            return Task.Status.RUNNING
        elif json == "COMPLETED":
            return Task.Status.COMPLETED
