from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from data_registry.models import Collection


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class ViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.collection = Collection.objects.create(
            title="Dirección Nacional de Contrataciones Públicas (DNCP)",
            title_en="National Directorate of Public Procurement (DNCP)",
            title_es="Dirección Nacional de Contrataciones Públicas (DNCP)",
            source_id="paraguay_dncp_records",
            public=True,
        )
        cls.job = cls.collection.job.create(
            active=True,
        )

    @patch("exporter.util.Export.get_files")
    def test_detail(self, get_files):
        get_files.return_value = {"jsonl": {"by_year": [{"year": 2022, "size": 1}]}}
        url = f"/en/publication/{self.collection.id}/download?name=2022.jsonl.gz"

        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection.id}")

        self.assertTemplateUsed("detail.html")
        self.assertContains(response, f"""<a href="{url}" rel="nofollow" download>2022</a>""", html=True)

    def test_publications_api(self):
        expected_response = {
            "id": self.collection.id,
            "title": self.collection.title_en,
            "source_id": self.collection.source_id,
            "update_frequency": Collection.UpdateFrequency.UNKNOWN.name,
            "country": "",
            "data_to": None,
            "data_from": None,
            "frozen": False,
            "language": "",
            "last_retrieved": None,
            "retrieval_frequency": "",
            "source_url": "",
            "region": "",
        }
        response = Client().get("/en/publications.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [expected_response])
        response = Client().get("/es/publications.json")
        self.assertEqual(response.status_code, 200)
        expected_response["title"] = self.collection.title_es
        self.assertEqual(response.json(), [expected_response])
        self.collection.delete()
        self.job.delete()

        for public, active_job in ((False, True), (True, False), (False, False)):
            with self.subTest(public=public, active_job=active_job):
                collection = Collection.objects.create(title="Test", public=public)
                if active_job:
                    collection.job.create(
                        active=True,
                    )
                response = Client().get("/es/publications.json")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [])
