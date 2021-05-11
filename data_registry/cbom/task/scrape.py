import requests
from django.conf import settings

from data_registry.cbom.task.task import BaseTask
from data_registry.models import Task


class Scrape(BaseTask):
    host = None
    job = None
    project = None

    def __init__(self, collection, job):
        if not settings.SCRAPY_HOST:
            raise Exception("SCRAPY_HOST is not set")
        if not settings.SCRAPY_PROJECT:
            raise Exception("SCRAPY_PROJECT is not set")

        self.job = job
        self.host = settings.SCRAPY_HOST
        self.project = settings.SCRAPY_PROJECT
        self.spider = collection.source_id

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

        jobid = json.get("jobid")

        self.job.context["job_id"] = jobid
        self.job.context["spider"] = self.spider
        self.job.context["scrapy_log"] = "{host}logs/{project}/{spider}/{jobid}.log".format(
            host=self.host, project=self.project, spider=self.spider, jobid=jobid
        )
        self.job.save()

    def get_status(self):
        resp = requests.get(
            self.host + "listjobs.json",
            params={
                "project": self.project
            }
        )

        json = resp.json()

        if json.get("status") == "error":
            raise Exception(json)

        jobid = self.job.context.get("job_id")

        if any(n["id"] == jobid for n in json.get("pending", [])):
            return Task.Status.WAITING
        if any(n["id"] == jobid for n in json.get("running", [])):
            return Task.Status.RUNNING
        if any(n["id"] == jobid for n in json.get("finished", [])):
            return Task.Status.COMPLETED

        raise Exception("Unable to get task state")