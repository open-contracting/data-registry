from unittest.mock import patch

from django.test import TransactionTestCase

from data_registry.cbom.process import process
from data_registry.cbom.task.task import BaseTask
from data_registry.models import Collection, Job, Task


class TestTask(BaseTask):
    def run(self):
        pass

    def get_status(self):
        return "COMPLETE"


class ProcessTests(TransactionTestCase):
    fixtures = ["data_registry/tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        with patch('data_registry.cbom.process.TaskFactory') as mock_factory:
            mock_factory.get_task.return_value = TestTask()

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
