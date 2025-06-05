from unittest.mock import patch

from django.db.models import RestrictedError
from django.test import TransactionTestCase

from data_registry.models import Collection
from tests import TestTask


class CollectionTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_is_out_of_date(self):
        collection = Collection.objects.get(pk=1)

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
