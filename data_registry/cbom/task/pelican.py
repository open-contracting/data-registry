from django.conf import settings

from data_registry.cbom.task.task import BaseTask
from data_registry.cbom.task.utils import request
from data_registry.models import Task


class Pelican(BaseTask):
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
            f"{settings.PELICAN_HOST}api/dataset_start",
            json={
                "name": self.get_pelican_dataset_name(),
                "collection_id": self.collection_id
            },
            error_msg=f"Unable to run Pelican for collection {self.job.collection}"
        )

    def get_status(self):
        pelican_id = self.get_pelican_id()
        if not pelican_id:
            return Task.Status.WAITING

        resp = request(
            "GET",
            f"{settings.PELICAN_HOST}api/dataset_status/{pelican_id}",
            error_msg=f"Unable get status of collection {self.job.collection} from Pelican"
        )

        json = resp.json().get("data")
        if not json:
            return Task.Status.WAITING

        state = json.get("state")
        phase = json.get("phase")

        if state == "FAILED":
            raise Exception("Pelican failed")

        if phase == "CHECKED" and state == "OK":
            return Task.Status.COMPLETED
        else:
            return Task.Status.RUNNING

    def get_pelican_id(self):
        pelican_id = self.job.context.get("pelican_id", None)
        if not pelican_id:
            resp = request(
                "POST",
                f"{settings.PELICAN_HOST}api/dataset_id",
                json={
                    "name": self.get_pelican_dataset_name()
                },
                error_msg="Unable to get pelican dataset id"
            )

            pelican_id = resp.json().get("data", None)
            if pelican_id:
                self.job.context["pelican_id"] = pelican_id
                self.job.save()

        return pelican_id

    def get_pelican_dataset_name(self):
        dataset_name = self.job.context.get("pelican_dataset_name", None)
        if not dataset_name:
            spider = self.job.context.get("spider")
            process_data_version = self.job.context.get("process_data_version")

            dataset_name = f"{spider}_{process_data_version}_{self.job.id}"

            self.job.context["pelican_dataset_name"] = dataset_name
            self.job.save()

        return dataset_name
