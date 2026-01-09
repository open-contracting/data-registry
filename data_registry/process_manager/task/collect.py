import logging
import os
import re
import shutil
from collections import Counter

import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.urls import reverse
from scrapyloganalyzer import ScrapyLogFile

from data_registry.exceptions import ConfigurationError, IrrecoverableError, RecoverableError, UnexpectedError
from data_registry.models import Job, Task, TaskNote
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from data_registry.util import CHANGE, scrapyd_url

logger = logging.getLogger(__name__)

PROJECT = settings.SCRAPYD["project"]
# https://github.com/open-contracting/kingfisher-collect/blob/7bfeba8/kingfisher_scrapy/extensions/kingfisher_process_api2.py#L117
PROCESS_ID = re.compile(r"Created collection (.+) in Kingfisher Process \(([^\)]+)\)")

IGNORE_WARNINGS = (
    "[scrapy.middleware] WARNING: Disabled kingfisher_scrapy.extensions.DatabaseStore: DATABASE_URL is not set.",
    "[yapw.clients] WARNING: Channel 1 was closed: ChannelClosedByClient: (200) 'Normal shutdown'",
)
# See LOG_CATEGORIES_PATTERN_DICT in https://github.com/my8100/logparser
# redirect_logs and retry_logs are ignored, and ignore_logs aren't observed.
# Note: log_categories might not contain all non-critical, non-error, non-warning messages.
# https://docs.scrapy.org/en/latest/topics/logging.html#log-levels
CATEGORY_LEVELS = {
    "critical_logs": TaskNote.Level.CRITICAL,
    "error_logs": TaskNote.Level.ERROR,
    "warning_logs": TaskNote.Level.WARNING,
}


def scrapyd_data(response):
    data = response.json()

    # *.json returns {"node_name": "ocp42.open-contracting.org", "status": "error", "message": "..."}
    # schedule.json returns {"status": "error", "message": "spider 'nonexistent' not found"}
    if data["status"] == "error":
        raise UnexpectedError(repr(data))

    return data


def get_message_type(category_name, message):
    if match := re.search(r"status=(\d{3})", message):
        return f"HTTP {match.group(1)}"

    for message_type, pattern in (
        # WARNING: Got data loss in {URL}. If you want to process broken responses set the setting
        # DOWNLOAD_FAIL_ON_DATALOSS = False -- This message won't be shown in further requests
        ("Data loss", "Got data loss"),
        # ERROR: Gave up retrying <GET {URL}> (failed 3 times): 503 Service Unavailable
        # (Typically paired with "status=###" or "Error downloading".)
        ("Retry failures", "Gave up retrying"),
        # ERROR: Error downloading <GET {URL}>
        # Traceback (most recent call last): …
        ("Download errors", "Error downloading"),
    ):
        if pattern in message:
            return message_type

    return category_name


class Collect(TaskManager):
    final_output = False

    def __init__(self, task):
        super().__init__(task)

        if not settings.SCRAPYD["url"]:
            raise ConfigurationError("SCRAPYD_URL is not set")
        if not settings.SCRAPYD["project"]:
            raise ConfigurationError("SCRAPYD_PROJECT is not set")

        self.spider = task.job.collection.source_id

    def read_log_file(self, scrapy_log_url):
        try:
            return self.request("get", scrapy_log_url, error_message="Unable to read Scrapy log").text
        except RecoverableError as e:
            # If the log file doesn't exist, the job can't continue.
            if (
                isinstance(e.__cause__, requests.HTTPError)
                and e.__cause__.response.status_code == requests.codes.not_found
            ):
                raise UnexpectedError("Scrapy log doesn't exist") from e
            raise

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

        scrapyd_job_id = data["jobid"]
        self.job.context["spider"] = self.spider
        self.job.context["job_id"] = scrapyd_job_id
        self.job.context["scrapy_log"] = scrapyd_url(f"logs/{PROJECT}/{self.spider}/{scrapyd_job_id}.log")
        self.job.save(update_fields=["modified", "context"])

    def get_status(self):
        scrapyd_job_id = self.job.context["job_id"]  # set in run()
        scrapy_log_url = self.job.context["scrapy_log"]  # set in run()

        response = self.request(
            "GET",
            scrapyd_url("status.json"),
            params={"job": scrapyd_job_id},
            error_message=f"Unable to get status of Scrapyd job {scrapyd_job_id}",
        )

        currstate = scrapyd_data(response)["currstate"]

        # If the job is pending, return early, because the log file will not exist yet.
        if currstate == "pending":
            return Task.Status.WAITING

        # Check early for the log file, to fail fast if Scrapyd somehow stalled without writing a log file.
        if "process_id" not in self.job.context and (match := PROCESS_ID.search(self.read_log_file(scrapy_log_url))):
            self.job.context["process_id"] = match.group(1)
            self.job.context["data_version"] = match.group(2)
            self.job.save(update_fields=["modified", "context"])

        if currstate == "running":
            return Task.Status.RUNNING

        if currstate == "finished":
            # If the collection ID or data version was irretrievable, the job can't continue.
            if "process_id" not in self.job.context or "data_version" not in self.job.context:
                raise UnexpectedError("Unable to retrieve collection ID and data version from Scrapy log")

            scrapy_log = ScrapyLogFile(scrapy_log_url, text=self.read_log_file(scrapy_log_url))

            logs = []
            notes = []
            counter = Counter()
            missing_next_link_error = False

            # These two are persisted on the Task itself.
            if not scrapy_log.is_finished():
                logs.append(f"crawl finish reason: {scrapy_log.logparser['finish_reason']}")
            if scrapy_log.error_rate > 0.01:  # 1%
                logs.append(f"crawl error rate: {scrapy_log.error_rate}")

            for key, level in (
                # For administrators to review "Dropped: Duplicate File" messages.
                ("item_dropped_count", TaskNote.Level.WARNING),
                # invalid_json_count is included in the error_rate.
                ("invalid_json_count", TaskNote.Level.ERROR),
            ):
                if value := scrapy_log.logparser["crawler_stats"].get(key):
                    logs.append(f"crawl {key}: {value}")

                    notes.append(TaskNote(task=self.task, level=level, note=f"{key}: {value}"))

            for category_name, category in scrapy_log.logparser["log_categories"].items():
                if category_name in {
                    # For example, australia_new_south_wales has http:// "next" URLs that redirect to https://.
                    # DEBUG-level only: https://github.com/scrapy/scrapy/blob/master/scrapy/downloadermiddlewares/redirect.py
                    "redirect_logs",
                    # Another message is already added to error_logs if RETRY_TIMES is exceeded.
                    # https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#std-setting-RETRY_TIMES
                    "retry_logs",
                }:
                    continue

                for message in category["details"]:
                    if not missing_next_link_error and "kingfisher_scrapy.exceptions.MissingNextLinkError" in message:
                        missing_next_link_error = True

                    if any(ignore in message for ignore in IGNORE_WARNINGS):
                        continue

                    message_type = get_message_type(category_name, message)

                    counter[message_type] += 1

                    notes.append(
                        TaskNote(
                            task=self.task,
                            level=CATEGORY_LEVELS.get(category_name, TaskNote.Level.UNKNOWN),
                            note=message,
                            data={"type": message_type},
                        )
                    )

            if logs or counter:
                path = reverse(CHANGE.format(content_type=ContentType.objects.get_for_model(Job)), args=[self.job.pk])
                url = f"https://{Site.objects.get_current().domain}{path}"
                messages = logs + [f"{message_type}: {count}" for message_type, count in counter.items()]
                logger.warning("%s has warnings\n%s\n    %s\n", self, url, "\n    ".join(messages))

            # Persist the task notes.

            # Delete any existing task notes, in case of retries.
            self.task.tasknote_set.all().delete()
            TaskNote.objects.bulk_create(notes)

            # Prevent further processing if acceptance criteria not met.

            if missing_next_link_error:
                raise IrrecoverableError("The crawl stopped prematurely")
            if not scrapy_log.is_finished():
                raise IrrecoverableError(f"The crawl wasn't finished: {scrapy_log.logparser['finish_reason']}")
            if scrapy_log.error_rate > 0.15:  # 15%
                raise IrrecoverableError(f"The crawl had a {scrapy_log.error_rate} error rate")

            return Task.Status.COMPLETED

        raise RecoverableError(f"Unable to find status of Scrapyd job {scrapyd_job_id}")

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
            error_message=f"Unable to cancel the Scrapyd job {scrapyd_job_id}",
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
            # The key was changed (010319f) prior to the most recent server move. This data is already wiped.
            if "process_data_version" not in self.job.context:
                logger.warning("%s: Unable to wipe crawl (data version is not set)", self)
            return

        data_version = self.job.context["data_version"]  # set in get_status()

        logger.info("%s: Wiping data for crawl %s", self, data_version)
        # 20010203_040506     Kingfisher Collect's FileStore extension
        # 2001-02-03 04:05:06 Kingfisher Collect's Kingfisher Process API extension
        # 2001-02-03T04:05:06 Kingfisher Process
        data_version = data_version.translate(str.maketrans(" T", "__", "-:"))
        spider_path = os.path.join(settings.KINGFISHER_COLLECT_FILES_STORE, self.spider)
        crawl_path = os.path.join(spider_path, data_version)
        if os.path.exists(crawl_path):
            try:
                shutil.rmtree(crawl_path)
                with os.scandir(spider_path) as it:
                    if not any(it):
                        os.rmdir(spider_path)
            except OSError as e:
                raise RecoverableError(f"Unable to wipe the Scrapyd job {scrapyd_job_id} at {crawl_path}") from e
