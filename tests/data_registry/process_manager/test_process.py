from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase, override_settings
from django.utils.timezone import now

from data_registry.exceptions import RecoverableError
from data_registry.models import Collection, Job, Task, TaskNote
from data_registry.process_manager import process
from tests import TestTask


class ProcessTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_task_progress(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_process.return_value = TestTask()

            self.assertTrue(collection.is_out_of_date())
            self.assertFalse(collection.job_set.incomplete())

            # First call initializes the job and runs the first task.
            process(collection)
            job = job_set.first()
            task = job.task_set.order_by("order").first()

            self.assertEqual(job.status, Job.Status.RUNNING)
            self.assertIsNotNone(job.start)
            self.assertIsNone(job.end)
            self.assertEqual(task.status, Task.Status.RUNNING)
            self.assertIsNotNone(task.start)
            self.assertIsNone(task.end)
            self.assertEqual("", task.result)
            self.assertFalse(collection.is_out_of_date())
            self.assertTrue(collection.job_set.incomplete())

            # Last call updates the status of the running task and job.
            process(collection)
            job = job_set.first()
            task = job.task_set.order_by("order").first()

            self.assertEqual(job.status, Job.Status.COMPLETED)
            self.assertIsNotNone(job.start)
            self.assertIsNotNone(job.end)
            self.assertEqual(task.status, Task.Status.COMPLETED)
            self.assertIsNotNone(task.start)
            self.assertIsNotNone(task.end)
            self.assertEqual("OK", task.result)
            self.assertFalse(collection.is_out_of_date())
            self.assertFalse(collection.job_set.incomplete())

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_delete_jobs(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with (
            patch("data_registry.process_manager.get_task_manager") as mock_process,
            patch("data_registry.signals.get_task_manager") as mock_delete,
        ):
            mock_process.return_value = mock_delete.return_value = TestTask()

            for deltas, keep_successful, keep_unsuccessful in (
                ([], set(), set()),
                # All old jobs after cut-off.
                ([500, 400], {400}, set()),
                # All old jobs before cut-off.
                ([100, 1], {1}, {100, 1}),
                # Old jobs before and after cut-uff.
                ([500, 400, 100, 1], {1}, {100, 1}),
            ):
                with self.subTest(deltas=deltas):
                    expected = []

                    # Create a pair of successful and unsuccessful jobs at each delta.
                    for days in deltas:
                        successful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        successful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.OK)
                        # Keep the second-most recent successful job.
                        if days in keep_successful:
                            expected.append(successful)

                        unsuccessful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        unsuccessful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.FAILED)
                        # Keep unsuccessful jobs for six months.
                        if days in keep_unsuccessful:
                            expected.append(unsuccessful)

                    # Create a new job that will complete after processing.
                    job = job_set.create(status=Job.Status.RUNNING, start=now())
                    job.task_set.update(status=Task.Status.RUNNING)
                    expected.append(job)

                    process(collection)

                    self.assertEqual(list(job_set.all()), expected)

                    # Delete jobs for the next subtest.
                    collection.active_job = None
                    collection.save()
                    job_set.all().delete()

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_delete_jobs_ocid_count(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        expected = []

        older_jobs = [
            (100, False),
            (1000, False),
            (1100, False),
            (1101, True),
            (1200, True),
        ]

        for ocid_count, should_keep in older_jobs:
            job = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=100))
            job.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.OK)
            job.coverage = {"/ocid": ocid_count}
            job.save()
            if should_keep:
                expected.append(job)

        # Create the second-most recent successful job.
        job = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=1))
        job.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.OK)
        job.coverage = {"/ocid": 0}
        job.save()
        expected.append(job)

        # Create a new job that will complete after processing, with 1000 OCIDs.
        job = job_set.create(status=Job.Status.RUNNING, start=now())
        job.task_set.update(status=Task.Status.RUNNING)
        job.coverage = {"/ocid": 1000}
        job.save()
        expected.append(job)

        with (
            patch("data_registry.process_manager.get_task_manager") as mock_process,
            patch("data_registry.signals.get_task_manager") as mock_delete,
            self.assertLogs("data_registry.process_manager", level="WARNING") as logs,
        ):
            mock_process.return_value = mock_delete.return_value = TestTask()

            process(collection)

            self.assertEqual(list(job_set.all()), expected)

            self.assertEqual(len(logs.records), 2)
            self.assertTrue(any("(1101 >> 1000)" in message for message in logs.output))
            self.assertTrue(any("(1200 >> 1000)" in message for message in logs.output))

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_irrecoverable_error(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        job = job_set.create(status=Job.Status.RUNNING)
        task = job.task_set.first()
        task.status = Task.Status.RUNNING
        task.save()

        def get_status():
            TaskNote.objects.bulk_create(
                [
                    TaskNote(task=task, level=TaskNote.Level.ERROR, note="HTTP 400 error", data={"type": "HTTP 400"}),
                    TaskNote(task=task, level=TaskNote.Level.ERROR, note="HTTP 500 error", data={"type": "HTTP 500"}),
                ]
            )
            return Task.Status.COMPLETED, "Test irrecoverable error"

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_manager = MagicMock()
            mock_manager.get_status.side_effect = get_status
            mock_process.return_value = mock_manager

            process(collection)

            task.refresh_from_db()
            job.refresh_from_db()

            self.assertEqual(task.status, Task.Status.COMPLETED)
            self.assertEqual(task.result, Task.Result.FAILED)
            self.assertEqual(task.note, "Test irrecoverable error")

            self.assertEqual(job.status, Job.Status.COMPLETED)

            self.assertEqual(
                list(TaskNote.objects.filter(task=task).values_list("level", "note", "data")),
                [
                    ("ERROR", "HTTP 400 error", {"type": "HTTP 400"}),
                    ("ERROR", "HTTP 500 error", {"type": "HTTP 500"}),
                ],
            )

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_recoverable_error(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        job = job_set.create(status=Job.Status.RUNNING)
        task = job.task_set.first()
        task.status = Task.Status.RUNNING
        task.save()

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_manager = MagicMock()
            mock_manager.get_status.side_effect = RecoverableError("Test recoverable error")
            mock_process.return_value = mock_manager

            process(collection)

            task.refresh_from_db()
            job.refresh_from_db()

            self.assertEqual(task.status, Task.Status.RUNNING)
            self.assertEqual(task.result, Task.Result.FAILED)
            self.assertEqual(task.note, "Test recoverable error")

            self.assertEqual(job.status, Job.Status.RUNNING)

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_exception(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        job = job_set.create(status=Job.Status.RUNNING)
        task = job.task_set.first()
        task.status = Task.Status.RUNNING
        task.save()

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_manager = MagicMock()
            mock_manager.get_status.side_effect = Exception("Test exception")
            mock_process.return_value = mock_manager

            process(collection)

            task.refresh_from_db()
            job.refresh_from_db()

            self.assertEqual(task.status, Task.Status.COMPLETED)
            self.assertEqual(task.result, Task.Result.FAILED)
            self.assertEqual(task.note, "Test exception")

            self.assertEqual(job.status, Job.Status.COMPLETED)

    @override_settings(JOB_TASKS_PLAN=["test"])
    def test_visit_all_jobs(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        job1 = job_set.create(status=Job.Status.RUNNING)
        task1 = job1.task_set.first()
        task1.status = Task.Status.RUNNING
        task1.save()

        job2 = job_set.create(status=Job.Status.RUNNING)
        task2 = job2.task_set.first()
        task2.status = Task.Status.RUNNING
        task2.save()

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_manager = MagicMock()
            mock_manager.get_status.side_effect = Exception("Test exception")
            mock_process.side_effect = [mock_manager, TestTask()]

            process(collection)

            task1.refresh_from_db()
            job1.refresh_from_db()
            task2.refresh_from_db()
            job2.refresh_from_db()

            self.assertEqual(task1.status, Task.Status.COMPLETED)
            self.assertEqual(task1.result, Task.Result.FAILED)

            self.assertEqual(job1.status, Job.Status.COMPLETED)

            self.assertEqual(task2.status, Task.Status.COMPLETED)
            self.assertEqual(task2.result, Task.Result.OK)

            self.assertEqual(job2.status, Job.Status.COMPLETED)
