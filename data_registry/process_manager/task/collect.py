import logging
import os
import re
import shutil
from datetime import date
from urllib.parse import urljoin

from django.conf import settings
from requests.exceptions import HTTPError

from data_registry.models import Task
from data_registry.process_manager.task.exceptions import RecoverableException
from data_registry.process_manager.task.task import BaseTask
from data_registry.process_manager.utils import request

logger = logging.getLogger(__name__)


class Collect(BaseTask):
    host = None
    job = None
    project = None
    collection = None

    def __init__(self, collection, job):
        if not settings.SCRAPYD["url"]:
            raise Exception("SCRAPYD_URL is not set")
        if not settings.SCRAPYD["project"]:
            raise Exception("SCRAPYD_PROJECT is not set")

        self.job = job
        self.host = settings.SCRAPYD["url"]
        self.project = settings.SCRAPYD["project"]
        self.spider = collection.source_id
        self.collection = collection

    def run(self):
        resp = request(
            "POST",
            urljoin(self.host, "schedule.json"),
            data={
                "project": self.project,
                "spider": self.spider,
                "steps": "compile",  # no "check"
            },
            error_msg=f"Unable to schedule scraping for project {self.project} and spider {self.spider}",
        )

        json = resp.json()
        if json.get("status") == "error":
            raise Exception(json)

        jobid = json.get("jobid")

        self.job.context["job_id"] = jobid
        self.job.context["spider"] = self.spider
        self.job.context["scrapy_log"] = urljoin(self.host, f"logs/{self.project}/{self.spider}/{jobid}.log")
        self.job.save()

        self.collection.last_update = date.today()
        self.collection.save()

    def get_status(self):
        jobid = self.job.context.get("job_id")
        process_id = self.job.context.get("process_id", None)

        if not process_id:
            process_id = self.get_process_id()
            self.job.context["process_id"] = process_id
            self.job.save()

        resp = request(
            "GET",
            urljoin(self.host, "listjobs.json"),
            params={"project": self.project},
            error_msg=f"Unable to get status of collect job #{jobid}",
        )

        json = resp.json()

        if json.get("status") == "error":
            raise Exception(json)

        if any(n["id"] == jobid for n in json.get("pending", [])):
            return Task.Status.WAITING
        if any(n["id"] == jobid for n in json.get("running", [])):
            return Task.Status.RUNNING
        if any(n["id"] == jobid for n in json.get("finished", [])):
            # process id must be set on the end of collect task
            if not process_id:
                raise Exception("Process id is not set")

            return Task.Status.COMPLETED

        raise RecoverableException("Collect job is in undefined state")

    def get_process_id(self):
        # process id is published in scrapy log
        log = self.job.context.get("scrapy_log", None)
        if not log:
            raise Exception("Scrapy log is not set")

        try:
            resp = request("get", log, error_msg=f"Unable to read scrapy log {log}")
        except RecoverableException as e:
            ex_cause = e.__cause__

            # If the request on the log file returns the error 404, something went wrong with the scrapy.
            # The file was probably lost, and the job will never be able to continue
            if isinstance(ex_cause, HTTPError) and ex_cause.response.status_code == 404:
                raise Exception("Scrapy log file doesn't exist")

            raise e
        # Must match
        # https://github.com/open-contracting/kingfisher-collect/blob/7b386e8e7a198a96b733e2d8437a814632db4def/kingfisher_scrapy/extensions.py#L541
        m = re.search("Created collection (.+) in Kingfisher Process", resp.text)
        return m.group(1) if m else None

    def wipe(self):
        version = self.job.context.get("process_data_version", None)
        if not version:
            logger.info("Unable to wipe COLLECT - process_data_version is not set")
            return

        logger.info("Wiping collect data for version %s.", version)

        version = version.replace("-", "").replace(":", "").replace("T", "_")

        path = f"{settings.KINGFISHER_COLLECT_FILES_STORE}/{self.spider}/{version}"

        if os.path.exists(path):
            shutil.rmtree(path)
