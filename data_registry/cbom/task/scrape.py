import logging
import os
import re
import shutil
from datetime import date

from django.conf import settings
from requests.exceptions import HTTPError

from data_registry.cbom.task.exceptions import RecoverableException
from data_registry.cbom.task.task import BaseTask
from data_registry.cbom.utils import request
from data_registry.models import Task

logger = logging.getLogger("scrape-task")


class Scrape(BaseTask):
    host = None
    job = None
    project = None
    collection = None

    def __init__(self, collection, job):
        if not settings.SCRAPY_HOST:
            raise Exception("SCRAPY_HOST is not set")
        if not settings.SCRAPY_PROJECT:
            raise Exception("SCRAPY_PROJECT is not set")

        self.job = job
        self.host = settings.SCRAPY_HOST
        self.project = settings.SCRAPY_PROJECT
        self.spider = collection.source_id
        self.collection = collection

    def run(self):
        resp = request(
            "POST",
            f"{self.host}schedule.json",
            data={
                "project": self.project,
                "spider": self.spider,
                "steps": "compile",  # no "check"
            },
            error_msg=f"Unable to schedule scraping for project {self.project} and spider {self.spider}"
        )

        json = resp.json()
        if json.get("status") == "error":
            raise Exception(json)

        jobid = json.get("jobid")

        self.job.context["job_id"] = jobid
        self.job.context["spider"] = self.spider
        self.job.context["scrapy_log"] = f"{self.host}logs/{self.project}/{self.spider}/{jobid}.log"
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
            f"{self.host}listjobs.json",
            params={
                "project": self.project
            },
            error_msg=f"Unable to get status of scrape job #{jobid}"
        )

        json = resp.json()

        if json.get("status") == "error":
            raise Exception(json)

        if any(n["id"] == jobid for n in json.get("pending", [])):
            return Task.Status.WAITING
        if any(n["id"] == jobid for n in json.get("running", [])):
            return Task.Status.RUNNING
        if any(n["id"] == jobid for n in json.get("finished", [])):
            # process id must be set on the end of scrape task
            if not process_id:
                raise Exception("Process id is not set")

            return Task.Status.COMPLETED

        raise RecoverableException("Scrape job is in undefined state")

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

        m = re.search('Created collection in Kingfisher process with id (.+)', resp.text)
        return m.group(1) if m else None

    def wipe(self):
        version = self.job.context.get("process_data_version", None)
        if not version:
            logger.info("Unable to wipe SCRAPE - process_data_version is not set")
            return

        logger.info("Wiping scrape data for version {}.".format(version))

        version = version.replace("-", "").replace(":", "").replace("T", "_")

        path = f"{settings.SCRAPY_FILES_STORE}/{self.spider}/{version}"

        if os.path.exists(path):
            shutil.rmtree(path)
