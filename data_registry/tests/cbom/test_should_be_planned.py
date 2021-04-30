from django.test import TransactionTestCase

from data_registry.cbom.process import should_be_planned
from data_registry.models import Collection


class ShouldBePlannedTests(TransactionTestCase):
    fixtures = ["data_registry/tests/fixtures/fixtures.json"]

    def test_happy_day(self):
        collection = Collection.objects.get(pk=1)

        self.assertTrue(should_be_planned(collection))
