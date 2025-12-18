from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.test import TransactionTestCase
from django.utils.timezone import now

from data_registry.models import Collection, Job, Task
from data_registry.process_manager import process
from tests import TestTask


class ProcessTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_task_progress(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with patch("data_registry.process_manager.get_task_manager") as mock_process:
            mock_process.return_value = TestTask()
            settings.JOB_TASKS_PLAN = ["test"]

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

    def test_delete_jobs(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with (
            patch("data_registry.process_manager.get_task_manager") as mock_process,
            patch("data_registry.signals.get_task_manager") as mock_delete,
        ):
            mock_process.return_value = mock_delete.return_value = TestTask()
            settings.JOB_TASKS_PLAN = ["test"]

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

    def test_delete_jobs_ocid_count(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with (
            patch("data_registry.process_manager.get_task_manager") as mock_process,
            patch("data_registry.signals.get_task_manager") as mock_delete,
        ):
            mock_process.return_value = mock_delete.return_value = TestTask()
            settings.JOB_TASKS_PLAN = ["test"]

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

            with self.assertLogs("data_registry.process_manager", level="WARNING") as logs:
                process(collection)

            self.assertEqual(list(job_set.all()), expected)

            self.assertEqual(len(logs.records), 2)
            self.assertTrue(any("(1101 >> 1000)" in message for message in logs.output))
            self.assertTrue(any("(1200 >> 1000)" in message for message in logs.output))
