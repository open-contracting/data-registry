from unittest.mock import patch

from django.conf import settings
from django.test import TransactionTestCase

from data_registry.models import Collection, Job, Task
from data_registry.process_manager.process import process


class TestTask:
    def run(self):
        pass

    def get_status(self):
        return Task.Status.COMPLETED

    def wipe(self):
        pass


class ProcessTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        with patch("data_registry.process_manager.process.get_runner") as mock_get_runner, patch(
            "data_registry.process_manager.process.update_collection_availability"
        ) as mock_update_collection_availability:
            # get_runner returns only TestTask
            mock_get_runner.return_value = TestTask()
            # skip update_collection_availability (does nothing, counts are not set!)
            mock_update_collection_availability.return_value = None
            # skip update_collection_metadaat (does nothing, metadata are not set!)

            settings.JOB_TASKS_PLAN = ["test"]

            # first call initializes job and runs first task
            process(collection)

            job = collection.job.first()

            # skip wipe
            job.keep_all_data = True
            job.save()

            self.assertIsNotNone(job)
            self.assertIsNotNone(job.start)

            task = job.task.order_by("order").first()

            self.assertEqual(Task.Status.RUNNING, task.status)
            self.assertIsNotNone(task.start)
            self.assertEqual("", task.result)

            # next call updates running task state
            process(collection)

            task = job.task.order_by("order").first()

            self.assertEqual(Task.Status.COMPLETED, task.status)
            self.assertIsNotNone(task.end)
            self.assertEqual("OK", task.result)

            # the job plan contains only one task, therefore the job should be completed
            # after completion of that task
            job = collection.job.first()
            self.assertIsNotNone(job.end)
            self.assertEqual(Job.Status.COMPLETED, job.status)
