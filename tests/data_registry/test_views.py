from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from data_registry.models import Collection, Job


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class ViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.collection = Collection.objects.create(
            title="Dirección Nacional de Contrataciones Públicas (DNCP)",
            source_id="paraguay_dncp_records",
            public=True,
        )
        cls.job = Job.objects.create(
            collection=cls.collection,
            active=True,
        )

    @patch("exporter.util.Export.get_files")
    def test_detail(self, get_files):
        get_files.return_value = {"jsonl": {"by_year": [{"year": 2022, "size": 1}]}}
        url = f"/api/download_export?spider=paraguay_dncp_records&job_id={self.job.id}&year=2022&suffix=jsonl.gz"

        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection.id}")

        self.assertTemplateUsed("detail.html")
        self.assertContains(response, f"""<a href="{url}" rel="nofollow" download>2022</a>""", html=True)
