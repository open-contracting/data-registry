import logging
import os
import re
import shutil
from urllib.parse import urljoin

from django.conf import settings
from requests.exceptions import HTTPError

from data_registry.exceptions import RecoverableException
from data_registry.models import Task
from data_registry.process_manager.util import TaskManager, skip_if_not_started

logger = logging.getLogger(__name__)

PROJECT = settings.SCRAPYD["project"]


def scrapyd_url(path):
    return urljoin(settings.SCRAPYD["url"], path)


def scrapyd_data(response):
    data = response.json()

    # *.json: {"node_name": "ocp42.open-contracting.org", "status": "error", "message": "..."}
    # schedule.json: {"status": "error", "message": "spider 'nonexistent' not found"}
    if data.get("status") == "error":
        raise Exception(repr(data))

    return data


class Collect(TaskManager):
    def __init__(self, task):
        super().__init__(task)

        if not settings.SCRAPYD["url"]:
            raise Exception("SCRAPYD_URL is not set")
        if not settings.SCRAPYD["project"]:
            raise Exception("SCRAPYD_PROJECT is not set")

        self.spider = task.job.collection.source_id

    @property
    def final_output(self):
        return False

    def run(self):
        response = self.request(
            "POST",
            scrapyd_url("schedule.json"),
            data={
                "project": PROJECT,
                "spider": self.spider,
                "steps": "compile",  # no "check"
            },
            error_message=f"Unable to schedule a Scrapyd job for project {PROJECT} and spider {self.spider}",
        )

        data = scrapyd_data(response)

        scrapyd_job_id = data.get("jobid")
        self.job.context["spider"] = self.spider
        self.job.context["job_id"] = scrapyd_job_id
        self.job.context["scrapy_log"] = scrapyd_url(f"logs/{PROJECT}/{self.spider}/{scrapyd_job_id}.log")
        self.job.save()

    def get_status(self):
        scrapyd_job_id = self.job.context["job_id"]  # set in run()
        scrapy_log_url = self.job.context["scrapy_log"]  # set in run()

        response = self.request(
            "GET",
            scrapyd_url("listjobs.json"),
            params={"project": PROJECT},
            error_message=f"Unable to get status of Scrapyd job #{scrapyd_job_id}",
        )

        data = scrapyd_data(response)

        # If the job is pending, return early, because the log file will not exist yet.
        if any(j["id"] == scrapyd_job_id for j in data.get("pending", [])):
            return Task.Status.WAITING

        # Check early for the log file, so that we can error if Scrapyd somehow stalled without writing a log file.
        if "process_id" not in self.job.context:
            try:
                response = self.request("get", scrapy_log_url, error_message="Unable to read Scrapy log")
            except RecoverableException as e:
                # If the log file doesn't exist, the job can't continue.
                if isinstance(e.__cause__, HTTPError) and e.__cause__.response.status_code == 404:
                    raise Exception("Scrapy log doesn't exist") from e
                raise

            # Must match
            # https://github.com/open-contracting/kingfisher-collect/blob/7bfeba8/kingfisher_scrapy/extensions/kingfisher_process_api2.py#L117
            if m := re.search(r"Created collection (.+) in Kingfisher Process \(([^\)]+)\)", response.text):
                self.job.context["process_id"] = m.group(1)
                self.job.context["data_version"] = m.group(2)
                self.job.save()

        if any(j["id"] == scrapyd_job_id for j in data.get("running", [])):
            return Task.Status.RUNNING

        if any(j["id"] == scrapyd_job_id for j in data.get("finished", [])):
            # If the collection ID or data version was irretrievable, the job can't continue.
            if "process_id" not in self.job.context or "data_version" not in self.job.context:
                raise Exception("Unable to retrieve collection ID and data version from Scrapy log")

            return Task.Status.COMPLETED

        raise RecoverableException(f"Unable to find status of Scrapyd job #{scrapyd_job_id}")

    @skip_if_not_started
    def wipe(self):
        scrapyd_job_id = self.job.context["job_id"]  # set in run()

        response = self.request(
            "POST",
            scrapyd_url("cancel.json"),
            data={
                "project": PROJECT,
                "job": scrapyd_job_id,
            },
            error_message=f"Unable to cancel the Scrapyd job #{self.job.context}",
        )

        scrapyd_data(response)  # raises for error message

        # `data_version` can be missing due to:
        #
        # - Irrecoverable errors
        #   - The Scrapyd job is gone
        #   - The log file doesn't exist
        #   - The request failed from Kingfisher Collect to Kingfisher Process
        # - Temporary errors
        #   - Scrapyd stopped responding after run()
        #   - Scrapyd returned an error message
        #   - wipe() was called before get_status() (or before get_status() sets `data_version`)
        #
        # The temporary errors are too rare to bother with.
        #
        # If the Scrapyd job was pending, there is nothing to wipe.
        if "data_version" not in self.job.context:
            logger.warning("%s: Unable to wipe crawl (data version is not set)", self)
            return

        data_version = self.job.context["data_version"]  # set in get_status()

        logger.info("%s: Wiping data for crawl %s", self, data_version)
        # 20010203_040506     Kingfisher Collect's FileStore extension
        # 2001-02-03 04:05:06 Kingfisher Collect's Kingfisher Process API extension
        # 2001-02-03T04:05:06 Kingfisher Process
        data_version = data_version.translate(str.maketrans(" T", "__", "-:"))
        path = f"{settings.KINGFISHER_COLLECT_FILES_STORE}/{self.spider}/{data_version}"
        if os.path.exists(path):
            shutil.rmtree(path)
