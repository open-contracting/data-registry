import logging
import os
import re
import shutil
from urllib.parse import urljoin

from django.conf import settings
from requests.exceptions import HTTPError

from data_registry.exceptions import RecoverableException
from data_registry.models import Task
from data_registry.process_manager.util import request

logger = logging.getLogger(__name__)


class Collect:
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
        response = request(
            "POST",
            urljoin(self.host, "schedule.json"),
            data={
                "project": self.project,
                "spider": self.spider,
                "steps": "compile",  # no "check"
            },
            error_msg=f"Unable to schedule scraping for project {self.project} and spider {self.spider}",
        )

        json = response.json()
        if json.get("status") == "error":
            raise Exception(json)

        job_id = json.get("jobid")

        self.job.context["job_id"] = job_id
        self.job.context["spider"] = self.spider
        self.job.context["scrapy_log"] = urljoin(self.host, f"logs/{self.project}/{self.spider}/{job_id}.log")
        self.job.save()

    def get_status(self):
        job_id = self.job.context.get("job_id")
        process_id = self.job.context.get("process_id")

        response = request(
            "GET",
            urljoin(self.host, "listjobs.json"),
            params={"project": self.project},
            error_msg=f"Unable to get status of collect job #{job_id}",
        )

        json = response.json()

        if json.get("status") == "error":
            raise Exception(json)

        if any(n["id"] == job_id for n in json.get("pending", [])):
            return Task.Status.WAITING

        # The log file does not exist if the job is pending.
        if not process_id:
            log = self.job.context.get("scrapy_log")

            try:
                response = request("get", log, error_msg=f"Unable to read scrapy log {log}")
            except RecoverableException as e:
                ex_cause = e.__cause__
                # If the request on the log file returns the error 404, something went wrong with the scrapy.
                # The file was probably lost, and the job will never be able to continue
                if isinstance(ex_cause, HTTPError) and ex_cause.response.status_code == 404:
                    raise Exception("Scrapy log file doesn't exist")
                raise e

            # Must match
            # https://github.com/open-contracting/kingfisher-collect/blob/7b386e8e7a198a96b733e2d8437a814632db4def/kingfisher_scrapy/extensions.py#L541
            m = re.search("Created collection (.+) in Kingfisher Process", response.text)
            process_id = m.group(1) if m else None

            self.job.context["process_id"] = process_id
            self.job.save()

        if any(n["id"] == job_id for n in json.get("running", [])):
            return Task.Status.RUNNING

        if any(n["id"] == job_id for n in json.get("finished", [])):
            if not process_id:
                raise Exception("Process id is not set")

            return Task.Status.COMPLETED

        raise RecoverableException("Collect job is in undefined state")

    def wipe(self):
        version = self.job.context.get("process_data_version")
        if not version:
            logger.warning("Unable to wipe COLLECT - process_data_version is not set")
            return

        logger.info("Wiping collect data for version %s.", version)

        version = version.replace("-", "").replace(":", "").replace("T", "_")

        path = f"{settings.KINGFISHER_COLLECT_FILES_STORE}/{self.spider}/{version}"

        if os.path.exists(path):
            shutil.rmtree(path)
