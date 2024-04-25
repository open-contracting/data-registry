from django.test import TransactionTestCase

from data_registry.models import Collection


class CollectionTests(TransactionTestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    def test_is_out_of_date(self):
        collection = Collection.objects.get(pk=1)

        self.assertTrue(collection.is_out_of_date())
