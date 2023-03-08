from django.test import TransactionTestCase

from data_registry.models import Collection
from data_registry.process_manager.process import should_be_planned


class ShouldBePlannedTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_happy_day(self):
        collection = Collection.objects.get(pk=1)

        self.assertTrue(should_be_planned(collection))
