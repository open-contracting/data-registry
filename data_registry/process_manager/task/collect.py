import logging
import os
import re
import shutil
from urllib.parse import urljoin

from django.conf import settings
from requests.exceptions import HTTPError

from data_registry.exceptions import RecoverableException
from data_registry.models import Task
from data_registry.process_manager.util import TaskManager

logger = logging.getLogger(__name__)


def scrapyd_url(path):
    return urljoin(settings.SCRAPYD["url"], path)


class Collect(TaskManager):
    def __init__(self, task):
        if not settings.SCRAPYD["url"]:
            raise Exception("SCRAPYD_URL is not set")
        if not settings.SCRAPYD["project"]:
            raise Exception("SCRAPYD_PROJECT is not set")

        super().__init__(task)
        self.spider = task.job.collection.source_id

    @property
    def final_output(self):
        return False

    def run(self):
        project = settings.SCRAPYD["project"]

        response = self.request(
            "POST",
            scrapyd_url("schedule.json"),
            data={
                "project": project,
                "spider": self.spider,
                "steps": "compile",  # no "check"
            },
            error_msg=f"Unable to schedule crawl for project {project} and spider {self.spider}",
        )

        data = response.json()
        if data.get("status") == "error":
            raise Exception(repr(data))

        scrapyd_job_id = data.get("jobid")
        self.job.context["spider"] = self.spider
        self.job.context["job_id"] = scrapyd_job_id
        self.job.context["scrapy_log"] = scrapyd_url(f"logs/{project}/{self.spider}/{scrapyd_job_id}.log")
        self.job.save()

    def get_status(self):
        scrapyd_job_id = self.job.context["job_id"]  # set in run()
        scrapy_log_url = self.job.context["scrapy_log"]  # set in run()

        response = self.request(
            "GET",
            scrapyd_url("listjobs.json"),
            params={"project": settings.SCRAPYD["project"]},
            error_msg=f"Unable to get status of Scrapyd job #{scrapyd_job_id}",
        )

        data = response.json()
        if data.get("status") == "error":
            raise Exception(repr(data))

        if any(j["id"] == scrapyd_job_id for j in data.get("pending", [])):
            return Task.Status.WAITING

        # The log file does not exist if the job is pending.
        if "process_id" not in self.job.context:
            try:
                response = self.request("get", scrapy_log_url, error_msg="Unable to read Scrapy log")
            except RecoverableException as e:
                # If the log file doesn't exist, the job can't continue onto other tasks.
                if isinstance(e.__cause__, HTTPError) and e.__cause__.response.status_code == 404:
                    raise Exception("Scrapy log doesn't exist") from e
                raise

            # Must match
            # https://github.com/open-contracting/kingfisher-collect/blob/3258ff4/kingfisher_scrapy/extensions/kingfisher_process_api2.py#L101
            if m := re.search("Created collection (.+) in Kingfisher Process", response.text):
                self.job.context["process_id"] = m.group(1)
                self.job.save()

        if any(j["id"] == scrapyd_job_id for j in data.get("running", [])):
            return Task.Status.RUNNING

        if any(j["id"] == scrapyd_job_id for j in data.get("finished", [])):
            # If the collection ID was irretrievable, the job can't continue onto other tasks.
            if "process_id" not in self.job.context:
                raise Exception("process_id is not set")

            return Task.Status.COMPLETED

        raise RecoverableException("Collect task has no status")

    def wipe(self):
        if "process_data_version" not in self.job.context:  # for example, if Process task never started
            logger.warning("%s: Unable to wipe crawl (data version is not set)", self)
            return

        data_version = self.job.context["process_data_version"]  # set in Process.get_status()

        logger.info("%s: Wiping data for crawl %s", self, data_version)
        data_version = data_version.replace("-", "").replace(":", "").replace("T", "_")
        path = f"{settings.KINGFISHER_COLLECT_FILES_STORE}/{self.spider}/{data_version}"
        if os.path.exists(path):
            shutil.rmtree(path)
