from django.test import TransactionTestCase

from data_registry.cbom.process import plan
from data_registry.models import Collection


class PlanTests(TransactionTestCase):
    fixtures = ["data_registry/tests/fixtures/fixtures.json"]

    def test(self):
        collection = Collection.objects.get(pk=1)

        plan(collection)

        self.assertIsNotNone(collection.job)
