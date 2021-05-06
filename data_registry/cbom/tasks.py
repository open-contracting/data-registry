import requests
from django.conf import settings


class TaskFactory:
    @staticmethod
    def get_task(job, task):
        type = task.type

        if type == "test":
            return Test()
        elif type == "scrape":
            return Scrape("{}-{}".format(job.id, task.id))
        else:
            raise Exception("Unsupported task type")


class Task:
    def run(self):
        raise Exception("Method is not implemented")

    def get_status(self):
        raise Exception("Method is not implemented")


class Test(Task):
    running = False

    def run(self):
        self.running = True

    def get_status(self):
        status = "RUNNING" if self.running else "COMPLETE"
        self.running = False
        return status


class Scrape(Task):
    host = None
    project = "kingfisher"
    jobid = None

    def __init__(self, jobid):
        if not jobid:
            raise Exception("jobid is required for Scrape task")
        if not settings.SCRAPY_HOST:
            raise Exception("SCRAPY_HOST is not set")

        self.jobid = jobid
        self.host = settings.SCRAPY_HOST

    def run(self):
        requests.post(
            self.host + "schedule.json",
            data={
                "project": self.project,
                "spider": "zambia",
                "jobid": self.jobid
            }
        )

    def get_status(self):
        resp = requests.get(
            self.host + "listjobs.json",
            data={
                "project": self.project
            }
        )

        json = resp.json()

        if any(n["id"] == self.jobid for n in json.get("pending", [])):
            return "WAITING"
        if any(n["id"] == self.jobid for n in json.get("running", [])):
            return "RUNNING"
        if any(n["id"] == self.jobid for n in json.get("finished", [])):
            return "COMPLETE"

        raise Exception("Unable to get task state")
