from datetime import timedelta
from unittest.mock import patch

from django.db.models import RestrictedError
from django.test import TransactionTestCase
from django.utils import timezone

from data_registry.models import Collection, Job, Task
from tests import TestTask

MONTHLY = Collection.RetrievalFrequency.MONTHLY


class CollectionTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_is_out_of_date(self):
        collection = Collection.objects.get(pk=1)

        self.assertTrue(collection.is_out_of_date())

    def test_is_out_of_date_frozen(self):
        for frozen, expected in ((True, False), (False, True)):
            with self.subTest(frozen=frozen):
                collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY, frozen=frozen)

                self.assertEqual(collection.is_out_of_date(), expected)

    def test_is_out_of_date_retrieval_frequency(self):
        for retrieval_frequency, expected in (("", False), (Collection.RetrievalFrequency.NEVER, False)):
            with self.subTest(retrieval_frequency=retrieval_frequency):
                collection = Collection.objects.create(title="test", retrieval_frequency=retrieval_frequency)

                self.assertEqual(collection.is_out_of_date(), expected)

    def test_is_out_of_date_incomplete_planned(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        collection.job_set.create(status=Job.Status.PLANNED, start=timezone.now() - timedelta(days=60))

        self.assertFalse(collection.is_out_of_date())

    def test_is_out_of_date_incomplete_running(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        collection.job_set.create(status=Job.Status.RUNNING, start=timezone.now() - timedelta(days=60))

        self.assertFalse(collection.is_out_of_date())

    def test_is_out_of_date_unsuccessful_less_than_one_week(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        job = collection.job_set.create(status=Job.Status.COMPLETED, start=timezone.now() - timedelta(days=5))
        job.task_set.create(status=Task.Status.COMPLETED, result=Task.Result.FAILED)

        self.assertFalse(collection.is_out_of_date())

    def test_is_out_of_date_unsuccessful_more_than_one_week(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        job = collection.job_set.create(status=Job.Status.COMPLETED, start=timezone.now() - timedelta(days=10))
        job.task_set.create(status=Task.Status.COMPLETED, result=Task.Result.FAILED)

        self.assertTrue(collection.is_out_of_date())

    def test_is_out_of_date_successful_less_than_frequency(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        job = collection.job_set.create(status=Job.Status.COMPLETED, start=timezone.now() - timedelta(days=15))
        job.task_set.create(status=Task.Status.COMPLETED, result=Task.Result.OK)

        self.assertFalse(collection.is_out_of_date())

    def test_is_out_of_date_successful_more_than_frequency(self):
        collection = Collection.objects.create(title="test", retrieval_frequency=MONTHLY)

        job = collection.job_set.create(status=Job.Status.COMPLETED, start=timezone.now() - timedelta(days=45))
        job.task_set.create(status=Task.Status.COMPLETED, result=Task.Result.OK)

        self.assertTrue(collection.is_out_of_date())

    def test_visible(self):
        self.assertEqual(Collection.objects.visible().count(), 0)

        Collection.objects.create(public=True)

        self.assertEqual(Collection.objects.visible().count(), 0)

        Collection.objects.create(public=True, no_data_rationale="nonempty")

        self.assertEqual(Collection.objects.visible().count(), 1)

        collection = Collection.objects.create(public=True)
        collection.active_job = collection.job_set.create()
        collection.save()

        self.assertEqual(Collection.objects.visible().count(), 2)


class JobTests(TransactionTestCase):
    @classmethod
    def setUp(cls):
        cls.collection = Collection.objects.create()
        cls.collection.active_job = cls.active_job = cls.collection.job_set.create()
        cls.collection.save()

        cls.inactive_job = cls.collection.job_set.create()

    def test_protect(self):
        with self.assertRaises(RestrictedError):
            self.active_job.delete()

        # Mock get_task_manager() to avoid NotImplementedError.
        with patch("data_registry.signals.get_task_manager") as mock_signals:
            mock_signals.return_value = TestTask()

            self.inactive_job.delete()
