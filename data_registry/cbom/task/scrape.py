import requests
from django.conf import settings

from data_registry.cbom.task.task import BaseTask


class Scrape(BaseTask):
    host = None
    task = None

    project = "kingfisher"

    def __init__(self, collection, task):
        if not settings.TASK_SCRAPE_HOST:
            raise Exception("TASK_SCRAPE_HOST is not set")

        self.task = task
        self.host = settings.TASK_SCRAPE_HOST
        self.spider = collection.spider

    def run(self):
        resp = requests.post(
            self.host + "schedule.json",
            data={
                "project": self.project,
                "spider": self.spider
            }
        )

        json = resp.json()
        if json.get("status") == "error":
            raise Exception(json)

        # set task context, contains "remote" jobid, it is required for status checking
        self.task.context = json
        self.task.save()

    def get_status(self):
        resp = requests.get(
            self.host + "listjobs.json",
            data={
                "project": self.project
            }
        )

        json = resp.json()

        if json.get("status") == "error":
            raise Exception(json)

        jobid = self.task.context.get("jobid")

        if any(n["id"] == jobid for n in json.get("pending", [])):
            return "WAITING"
        if any(n["id"] == jobid for n in json.get("running", [])):
            return "RUNNING"
        if any(n["id"] == jobid for n in json.get("finished", [])):
            return "COMPLETE"

        raise Exception("Unable to get task state")
