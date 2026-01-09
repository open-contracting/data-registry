from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase, override_settings

from data_registry.exceptions import IrrecoverableError, UnexpectedError
from data_registry.models import Collection, Task, TaskNote
from data_registry.process_manager.task.collect import Collect


@override_settings(SCRAPYD={"url": "http://localhost:6800", "project": "test_project"})
class CollectTaskTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_get_status_pending(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {"job_id": "test-job-id", "scrapy_log": "http://example.com/log.txt"}

        collect_manager = Collect(task)

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "pending"}

        with patch.object(collect_manager, "request", return_value=mock_response):
            status = collect_manager.get_status()

        self.assertEqual(status, Task.Status.WAITING)

    def test_get_status_running(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {"job_id": "test-job-id", "scrapy_log": "http://example.com/log.txt"}

        collect_manager = Collect(task)

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "running"}
        log_content = "Created collection 456 in Kingfisher Process (2024-01-15 10:00:00)"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
        ):
            status = collect_manager.get_status()

        job.refresh_from_db()

        self.assertEqual(status, Task.Status.RUNNING)
        self.assertEqual(task.job.context["process_id"], "456")
        self.assertEqual(task.job.context["data_version"], "2024-01-15 10:00:00")

    def test_get_status_running_with_process_id(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {
            "job_id": "test-job-id",
            "scrapy_log": "http://example.com/log.txt",
            "process_id": "123",
            "data_version": "2024-01-01",
        }

        collect_manager = Collect(task)

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "running"}

        with patch.object(collect_manager, "request", return_value=mock_response):
            status = collect_manager.get_status()

        self.assertEqual(status, Task.Status.RUNNING)

    def test_get_status_finished_without_process_id(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {"job_id": "test-job-id", "scrapy_log": "http://example.com/log.txt"}

        collect_manager = Collect(task)

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "finished"}
        log_content = "Some log without collection ID"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
            self.assertRaisesMessage(
                UnexpectedError, "Unable to retrieve collection ID and data version from Scrapy log"
            ),
        ):
            collect_manager.get_status()

    def test_get_status_finished_with_missing_next_link_error(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {
            "job_id": "test-job-id",
            "scrapy_log": "http://example.com/log.txt",
            "process_id": "123",
            "data_version": "2024-01-01",
        }

        collect_manager = Collect(task)

        mock_scrapy_log = MagicMock()
        mock_scrapy_log.is_finished.return_value = True
        mock_scrapy_log.error_rate = 0.05
        mock_scrapy_log.logparser = {
            "finish_reason": "finished",
            "crawler_stats": {},
            "log_categories": {
                "error_logs": {
                    "details": [
                        "2024-01-15 12:00:00 [scrapy.core.scraper] ERROR: "
                        "kingfisher_scrapy.exceptions.MissingNextLinkError"
                    ]
                }
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "finished"}
        log_content = "Created collection 123 in Kingfisher Process (2024-01-01)"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
            patch("data_registry.process_manager.task.collect.ScrapyLogFile", return_value=mock_scrapy_log),
            self.assertRaisesMessage(IrrecoverableError, "The crawl stopped prematurely"),
        ):
            collect_manager.get_status()

    def test_get_status_finished_not_finished(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {
            "job_id": "test-job-id",
            "scrapy_log": "http://example.com/log.txt",
            "process_id": "123",
            "data_version": "2024-01-01",
        }

        collect_manager = Collect(task)

        mock_scrapy_log = MagicMock()
        mock_scrapy_log.is_finished.return_value = False
        mock_scrapy_log.error_rate = 0.05
        mock_scrapy_log.logparser = {
            "finish_reason": "shutdown",
            "crawler_stats": {},
            "log_categories": {},
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "finished"}
        log_content = "Created collection 123 in Kingfisher Process (2024-01-01)"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
            patch("data_registry.process_manager.task.collect.ScrapyLogFile", return_value=mock_scrapy_log),
            self.assertRaisesMessage(IrrecoverableError, "The crawl wasn't finished: shutdown"),
        ):
            collect_manager.get_status()

    def test_get_status_finished_error_rate(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {
            "job_id": "test-job-id",
            "scrapy_log": "http://example.com/log.txt",
            "process_id": "123",
            "data_version": "2024-01-01",
        }

        collect_manager = Collect(task)

        mock_scrapy_log = MagicMock()
        mock_scrapy_log.is_finished.return_value = True
        mock_scrapy_log.error_rate = 0.20
        mock_scrapy_log.logparser = {
            "finish_reason": "finished",
            "crawler_stats": {},
            "log_categories": {},
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "finished"}
        log_content = "Created collection 123 in Kingfisher Process (2024-01-01)"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
            patch("data_registry.process_manager.task.collect.ScrapyLogFile", return_value=mock_scrapy_log),
            self.assertRaisesMessage(IrrecoverableError, "The crawl had a 0.2 error rate"),
        ):
            collect_manager.get_status()

    def test_get_status_finished_success(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()
        task.job.context = {
            "job_id": "test-job-id",
            "scrapy_log": "http://example.com/log.txt",
            "process_id": "123",
            "data_version": "2024-01-01",
        }

        task.tasknote_set.create(level="WARNING", note="Old note to be deleted")

        collect_manager = Collect(task)

        mock_scrapy_log = MagicMock()
        mock_scrapy_log.is_finished.return_value = True
        mock_scrapy_log.error_rate = 0.05
        mock_scrapy_log.logparser = {
            "finish_reason": "finished",
            "crawler_stats": {
                "item_dropped_count": 10,
                "invalid_json_count": 5,
            },
            "log_categories": {
                "error_logs": {
                    "details": [
                        "2024-01-15 12:00:00 [scrapy.core.scraper] ERROR: status=404 url=http://example.com/1",
                        "2024-01-15 12:00:01 [scrapy.core.scraper] ERROR: status=404 url=http://example.com/2",
                        "2024-01-15 12:00:02 [scrapy.core.scraper] ERROR: status=500 url=http://example.com/3",
                        "2024-01-15 12:00:03 [scrapy.core.scraper] ERROR: Error downloading <GET http://example.com>",
                        "2024-01-15 12:00:04 [scrapy.core.scraper] ERROR: Gave up retrying <GET http://example.com>",
                    ]
                },
                "warning_logs": {
                    "details": [
                        "2024-01-15 12:00:05 [scrapy.core.scraper] WARNING: Got data loss in http://example.com",
                        "[scrapy.middleware] WARNING: Disabled kingfisher_scrapy.extensions.DatabaseStore: "
                        "DATABASE_URL is not set.",
                        "[yapw.clients] WARNING: Channel 1 was closed: ChannelClosedByClient: (200) 'Normal shutdown'",
                    ]
                },
                "redirect_logs": {"details": ["2024-01-15 12:00:00 [scrapy] INFO: Redirect from http to https"]},
                "retry_logs": {"details": ["2024-01-15 12:00:01 [scrapy] DEBUG: Retrying request"]},
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "currstate": "finished"}
        log_content = "Created collection 123 in Kingfisher Process (2024-01-01)"

        with (
            patch.object(collect_manager, "request", return_value=mock_response),
            patch.object(collect_manager, "read_log_file", return_value=log_content),
            patch("data_registry.process_manager.task.collect.ScrapyLogFile", return_value=mock_scrapy_log),
        ):
            status = collect_manager.get_status()

        self.assertEqual(status, Task.Status.COMPLETED)
        self.assertEqual(
            list(TaskNote.objects.filter(task=task).values_list("level", "note", "data")),
            [
                ("WARNING", "item_dropped_count: 10", {}),
                ("ERROR", "invalid_json_count: 5", {}),
                (
                    "ERROR",
                    "2024-01-15 12:00:00 [scrapy.core.scraper] ERROR: status=404 url=http://example.com/1",
                    {"type": "HTTP 404"},
                ),
                (
                    "ERROR",
                    "2024-01-15 12:00:01 [scrapy.core.scraper] ERROR: status=404 url=http://example.com/2",
                    {"type": "HTTP 404"},
                ),
                (
                    "ERROR",
                    "2024-01-15 12:00:02 [scrapy.core.scraper] ERROR: status=500 url=http://example.com/3",
                    {"type": "HTTP 500"},
                ),
                (
                    "ERROR",
                    "2024-01-15 12:00:03 [scrapy.core.scraper] ERROR: Error downloading <GET http://example.com>",
                    {"type": "Download errors"},
                ),
                (
                    "ERROR",
                    "2024-01-15 12:00:04 [scrapy.core.scraper] ERROR: Gave up retrying <GET http://example.com>",
                    {"type": "Retry failures"},
                ),
                (
                    "WARNING",
                    "2024-01-15 12:00:05 [scrapy.core.scraper] WARNING: Got data loss in http://example.com",
                    {"type": "Data loss"},
                ),
            ],
        )
