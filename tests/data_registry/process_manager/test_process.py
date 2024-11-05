from unittest.mock import patch

from django.conf import settings
from django.test import TransactionTestCase

from data_registry.models import Collection, Job, Task
from data_registry.process_manager import process
from tests import TestTask


class ProcessTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        with patch("data_registry.process_manager.get_task_manager") as mock_get_task_manager:
            mock_get_task_manager.return_value = TestTask()

            settings.JOB_TASKS_PLAN = ["test"]

            # first call initializes job and runs first task
            process(collection)

            job = collection.job_set.first()

            # skip wipe
            job.keep_all_data = True
            job.save()

            self.assertIsNotNone(job)
            self.assertIsNotNone(job.start)

            task = job.task_set.order_by("order").first()

            self.assertEqual(Task.Status.RUNNING, task.status)
            self.assertIsNotNone(task.start)
            self.assertEqual("", task.result)

            # next call updates running task state
            process(collection)

            task = job.task_set.order_by("order").first()

            self.assertEqual(Task.Status.COMPLETED, task.status)
            self.assertIsNotNone(task.end)
            self.assertEqual("OK", task.result)

            # the job plan contains only one task, therefore the job should be completed
            # after completion of that task
            job = collection.job_set.first()
            self.assertIsNotNone(job.end)
            self.assertEqual(Job.Status.COMPLETED, job.status)
