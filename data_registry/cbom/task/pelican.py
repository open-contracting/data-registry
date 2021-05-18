import requests
from django.conf import settings
from requests.models import HTTPError

from data_registry.cbom.task.task import BaseTask
from data_registry.models import Task


class Pelican(BaseTask):
    job = None
    process_id = None

    def __init__(self, job):
        self.job = job
        self.process_id = self.job.context.get("process_id")
        if not self.process_id:
            raise Exception("Process id is not set")

    def run(self):
        try:
            resp = requests.post(
                f"{settings.PELICAN_HOST}api/dataset_start",
                json={
                    "name": self.pelican_dataset_name(),
                    "collection_id": self.process_id
                })
            resp.raise_for_status()
        except HTTPError as e:
            raise Exception(f"Unable to run Pelican for collection {self.job.collection}") from e

    def get_status(self):
        try:
            resp = requests.get(f"{settings.PELICAN_HOST}api/dataset_progress/{self.process_id}")
            resp.raise_for_status()

            json = resp.json()
            state = json.get("state")
            phase = json.get("phase")

            if state == "FAILED":
                raise Exception("Pelican failed")

            if phase == "CHECKED" and state == "OK":
                return Task.Status.COMPLETED
            else:
                return Task.Status.RUNNING
        except HTTPError as e:
            raise Exception(f"Unable get status of collection {self.job.collection} from Pelican") from e

    def pelican_dataset_name(self):
        spider = self.job.context.get("spider")
        process_data_version = self.job.context.get("process_data_version")

        return f"{spider}_{process_data_version}"
