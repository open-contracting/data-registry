from django.test import TransactionTestCase

from data_registry.models import Collection
from data_registry.process_manager.process import plan


class PlanTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        plan(collection)

        self.assertIsNotNone(collection.job)
