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

        tasks = Task.objects.filter(job=job).order_by("order")

        self.assertEqual("RUNNING", tasks[0].status)
        self.assertIsNotNone(tasks[0].start)
        self.assertIsNone(tasks[0].result)

        # next call updates running task state
        process(collection)

        tasks = Task.objects.filter(job=job).order_by("order")

        self.assertEqual("COMPLETED", tasks[0].status)
        self.assertIsNotNone(tasks[0].end)
        self.assertEqual("OK", tasks[0].result)

        # the job plan contains only one task, therefore the job should be completed
        # after completion of that task
        job = Job.objects.filter(collection=collection).first()
        self.assertIsNotNone(job.end)
        self.assertEqual("COMPLETED", job.status)
