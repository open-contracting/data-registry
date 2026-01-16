from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase

from data_registry.models import Collection, Task, TaskNote
from data_registry.process_manager.task.process import Process


class ProcessTaskTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_get_status_no_compiled_collection(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()

        process_manager = Process(task)
        process_manager.job.context = {"process_id": 1}

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "transform_type": "", "completed_at": "2024-01-01T00:00:00Z", "expected_files_count": 1}
        ]

        with patch.object(process_manager, "request", return_value=mock_response):
            status, failure_reason = process_manager.get_status()

        self.assertEqual(status, Task.Status.COMPLETED)
        self.assertEqual(failure_reason, "No compiled collection")

    def test_get_status_running(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()

        process_manager = Process(task)
        process_manager.job.context = {"process_id": 1}

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "transform_type": "", "completed_at": None, "expected_files_count": 1},
            {"id": 2, "transform_type": "compile-releases", "completed_at": None},
        ]

        with patch.object(process_manager, "request", return_value=mock_response):
            status, failure_reason = process_manager.get_status()

        self.assertEqual(status, Task.Status.RUNNING)
        self.assertIsNone(failure_reason)

    def test_get_status_collection_is_empty(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()

        process_manager = Process(task)
        process_manager.job.context = {"process_id": 1}

        mock_response = MagicMock()
        mock_response.json.side_effect = [
            # tree response
            [
                {"id": 1, "transform_type": "", "completed_at": "2024-01-01T00:00:00Z", "expected_files_count": 0},
                {"id": 2, "transform_type": "compile-releases", "completed_at": "2024-01-01T00:00:00Z"},
            ],
            # metadata response
            {},
            # notes response
            {"WARNING": [], "ERROR": []},
        ]

        with patch.object(process_manager, "request", return_value=mock_response):
            status, failure_reason = process_manager.get_status()

        self.assertEqual(status, Task.Status.COMPLETED)
        self.assertEqual(failure_reason, "Collection is empty")

    def test_get_status_completed(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()

        task.tasknote_set.create(level="WARNING", note="Old note that is expected to be deleted 1")
        task.tasknote_set.create(level="ERROR", note="Old note that is expected to be deleted 2")

        process_manager = Process(task)
        process_manager.job.context = {"process_id": 1}

        mock_response = MagicMock()
        mock_response.json.side_effect = [
            # tree response
            [
                {
                    "id": 1,
                    "transform_type": "",
                    "completed_at": "2024-01-01T00:00:00Z",
                    "expected_files_count": 1,
                },
                {
                    "id": 2,
                    "transform_type": "compile-releases",
                    "completed_at": "2024-01-01T00:00:00Z",
                },
            ],
            # metadata response
            {
                "published_from": "2024-01-01",
                "published_to": "2024-12-31",
                "license": "CC-BY-4.0",
                "publication_policy": "https://example.com/publication-policy",
                "ocid_prefix": "ocds-213czf",
            },
            # notes response
            {
                "WARNING": [
                    [
                        "Warning 1",
                        {"type": "DuplicateIdValueWarning", "paths": {"/releases/0/id": 5, "/releases/1/id": 3}},
                    ],
                    [
                        "Warning 2",
                        {"type": "DuplicateIdValueWarning", "paths": {"/releases/0/id": 2}},
                    ],
                    ["Warning 3", {"type": "OtherType", "data": "test data"}],
                ],
                "ERROR": [["Error 1", {"type": "ErrorType", "message": "test message"}]],
            },
        ]

        with patch.object(process_manager, "request", return_value=mock_response):
            status, failure_reason = process_manager.get_status()

        task_notes = TaskNote.objects.filter(task=task).order_by("level", "note")
        warning_notes = task_notes.filter(level="WARNING")
        error_notes = task_notes.filter(level="ERROR")
        merge_notes = warning_notes.filter(note="OCDS Merge").order_by("data__path")
        other_notes = warning_notes.exclude(note="OCDS Merge")
        job.refresh_from_db()

        self.assertEqual(task_notes.count(), 4)
        self.assertEqual(warning_notes.count(), 3)

        self.assertEqual(merge_notes.count(), 2)
        self.assertEqual(merge_notes[0].task_id, task.id)
        self.assertEqual(merge_notes[0].data, {"path": "/releases/0/id", "count": 7})
        self.assertEqual(merge_notes[1].task_id, task.id)
        self.assertEqual(merge_notes[1].data, {"path": "/releases/1/id", "count": 3})

        self.assertEqual(other_notes.count(), 1)
        self.assertEqual(other_notes[0].task_id, task.id)
        self.assertEqual(other_notes[0].note, "Warning 3")
        self.assertEqual(other_notes[0].data, {"type": "OtherType", "data": "test data"})

        self.assertEqual(error_notes.count(), 1)
        self.assertEqual(error_notes[0].task_id, task.id)
        self.assertEqual(error_notes[0].note, "Error 1")
        self.assertEqual(error_notes[0].data, {"type": "ErrorType", "message": "test message"})

        self.assertEqual(job.context["process_compiled_collection_id"], 2)
        self.assertEqual(str(job.date_from), "2024-01-01")
        self.assertEqual(str(job.date_to), "2024-12-31")
        self.assertEqual(job.license, "CC-BY-4.0")
        self.assertEqual(job.publication_policy, "https://example.com/publication-policy")
        self.assertEqual(job.ocid_prefix, "ocds-213czf")

        self.assertEqual(status, Task.Status.COMPLETED)
        self.assertIsNone(failure_reason)

    def test_get_status_empty_metadata(self):
        collection = Collection.objects.get(pk=1)
        job = collection.job_set.create()
        task = job.task_set.order_by("order").first()

        task.tasknote_set.create(level="WARNING", note="Old note that is expected to be deleted 1")
        task.tasknote_set.create(level="ERROR", note="Old note that is expected to be deleted 2")

        process_manager = Process(task)
        process_manager.job.context = {"process_id": 1}

        mock_response = MagicMock()
        mock_response.json.side_effect = [
            # tree response
            [
                {"id": 1, "transform_type": "", "completed_at": "2024-01-01T00:00:00Z", "expected_files_count": 1},
                {"id": 2, "transform_type": "compile-releases", "completed_at": "2024-01-01T00:00:00Z"},
            ],
            # metadata response
            {},
            # notes response
            {"WARNING": [], "ERROR": []},
        ]

        with patch.object(process_manager, "request", return_value=mock_response):
            status, failure_reason = process_manager.get_status()

        task_notes = TaskNote.objects.filter(task=task).order_by("level", "note")
        job.refresh_from_db()

        self.assertEqual(task_notes.count(), 0)

        self.assertEqual(job.context["process_compiled_collection_id"], 2)
        self.assertIsNone(job.date_from)
        self.assertIsNone(job.date_to)
        self.assertEqual(job.license, "")
        self.assertEqual(job.publication_policy, "")
        self.assertEqual(job.ocid_prefix, "")

        self.assertEqual(status, Task.Status.COMPLETED)
        self.assertIsNone(failure_reason)
