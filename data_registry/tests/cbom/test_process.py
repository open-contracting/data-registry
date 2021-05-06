from django.test import TransactionTestCase

from data_registry.cbom.process import process
from data_registry.models import Collection, Job, Task


class ProcessTests(TransactionTestCase):
    fixtures = ["data_registry/tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        # first call initializes job and runs first task
        process(collection)

        job = Job.objects.filter(collection=collection).first()
        self.assertIsNotNone(job)
        self.assertIsNotNone(job.start)

        task = Task.objects.filter(job=job).order_by("order").first()

        self.assertEqual("RUNNING", task.status)
        self.assertIsNotNone(task.start)
        self.assertIsNone(task.result)

        # next call updates running task state
        process(collection)

        task = Task.objects.filter(job=job).order_by("order").first()

        self.assertEqual("COMPLETED", task.status)
        self.assertIsNotNone(task.end)
        self.assertEqual("OK", task.result)

        # the job plan contains only one task, therefore the job should be completed
        # after completion of that task
        job = Job.objects.filter(collection=collection).first()
        self.assertIsNotNone(job.end)
        self.assertEqual("COMPLETED", job.status)
