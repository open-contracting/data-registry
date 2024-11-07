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

    def test_delete_jobs(self):
        collection = Collection.objects.get(pk=1)
        job_set = collection.job_set

        with (
            patch("data_registry.process_manager.get_task_manager") as mock_process,
            patch("data_registry.signals.get_task_manager") as mock_delete,
        ):
            mock_process.return_value = mock_delete.return_value = TestTask()
            settings.JOB_TASKS_PLAN = ["test"]

            for delete, keep in (([], []), ([], [500]), ([], [100]), ([500, 400], [200, 100])):
                with self.subTest(delete=delete, keep=keep):
                    expected = []

                    # Create a new job that will complete after processing.
                    job = job_set.create(status=Job.Status.RUNNING, start=now())
                    job.task_set.update(status=Task.Status.RUNNING)
                    expected.append(job)

                    # Create some jobs that completed successfully and unsuccessfully.
                    for days in keep:
                        successful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        successful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.OK)
                        # An old, successful job is kept, if it is the other most recent successful job.
                        expected.append(successful)

                        unsuccessful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        unsuccessful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.FAILED)
                        if days <= 365:  # An old, unsuccessful job is deleted, unconditionally.
                            expected.append(unsuccessful)

                    # Create old jobs that completed successfully and unsuccessfully.
                    for days in delete:
                        successful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        successful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.OK)

                        unsuccessful = job_set.create(status=Job.Status.COMPLETED, start=now() - timedelta(days=days))
                        unsuccessful.task_set.update(status=Task.Status.COMPLETED, result=Task.Result.FAILED)

                    process(collection)

                    self.assertEqual(list(job_set.all()), expected)

                    # Delete jobs for the next subtest.
                    collection.active_job = None
                    collection.save()
                    job_set.all().delete()
