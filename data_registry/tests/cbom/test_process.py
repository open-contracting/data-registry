from unittest.mock import patch

from django.conf import settings
from django.test import TransactionTestCase

from data_registry.cbom.process import process
from data_registry.cbom.task.task import BaseTask
from data_registry.models import Collection, Job, Task


class TestTask(BaseTask):
    def run(self):
        pass

    def get_status(self):
        return Task.Status.COMPLETED


class ProcessTests(TransactionTestCase):
    fixtures = ["data_registry/tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        with patch('data_registry.cbom.process.TaskFactory') as mock_factory,\
             patch('data_registry.cbom.process.update_collection_availability')\
                as mock_update_collection_availability,\
             patch('data_registry.cbom.process.update_collection_metadata') as mock_update_collection_metadata:
            # factory returns only TestTask
            mock_factory.get_task.return_value = TestTask()
            # skip update_collection_availability (does nothing, counts are not set!)
            mock_update_collection_availability.return_value = None
            # skip update_collection_metadaat (does nothing, metadata are not set!)
            mock_update_collection_metadata.return_value = None

            settings.JOB_TASKS_PLAN = ["test"]

            # first call initializes job and runs first task
            process(collection)

            job = Job.objects.filter(collection=collection).first()
            self.assertIsNotNone(job)
            self.assertIsNotNone(job.start)

            task = Task.objects.filter(job=job).order_by("order").first()

            self.assertEqual(Task.Status.RUNNING, task.status)
            self.assertIsNotNone(task.start)
            self.assertIsNone(task.result)

            # next call updates running task state
            process(collection)

            task = Task.objects.filter(job=job).order_by("order").first()

            self.assertEqual(Task.Status.COMPLETED, task.status)
            self.assertIsNotNone(task.end)
            self.assertEqual("OK", task.result)

            # the job plan contains only one task, therefore the job should be completed
            # after completion of that task
            job = Job.objects.filter(collection=collection).first()
            self.assertIsNotNone(job.end)
            self.assertEqual(Job.Status.COMPLETED, job.status)
