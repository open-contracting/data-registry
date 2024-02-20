import datetime
from unittest.mock import patch

from django.test import Client, TestCase, override_settings

from data_registry import models


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class ViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.collection = models.Collection.objects.create(
            public=True,
            # Identification
            title="Ignore",
            title_en="National Directorate of Public Procurement (DNCP)",
            title_es="Dirección Nacional de Contrataciones Públicas (DNCP)",
            country="Ignore",
            country_en="Paraguay (EN)",
            country_es="Paraguay (ES)",
            # Accrual periodicity
            last_retrieved=datetime.date(2001, 2, 3),
            retrieval_frequency=models.Collection.RetrievalFrequency.MONTHLY,
            # Provenance
            source_id="paraguay_dncp_records",
            source_url="https://contrataciones.gov.py/datos/api/v3/doc/",
            # Other details
            region=models.Collection.Region.LAC,
            language="Ignore",
            language_en="Spanish",
            language_es="Español",
        )
        cls.job = cls.collection.job.create(
            active=True,
            date_from=datetime.date(2010, 2, 1),
            date_to=datetime.date(2023, 9, 30),
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
        extra_job = self.collection.job.create(active=True)

        en_response = Client().get("/en/publications.json")
        es_response = Client().get("/es/publications.json")

        extra_job.delete()

        expected = {
            # Identification
            "id": self.collection.id,
            "title": "National Directorate of Public Procurement (DNCP)",
            "country": "Paraguay (EN)",
            # Accrual periodicity
            "last_retrieved": "2001-02-03",
            "retrieval_frequency": "MONTHLY",
            "update_frequency": "UNKNOWN",
            "frozen": False,
            # Provenance
            "source_id": "paraguay_dncp_records",
            "source_url": "https://contrataciones.gov.py/datos/api/v3/doc/",
            # Other details
            "region": "LAC",
            "language": "Spanish",
            "date_from": "2010-02-01",
            "date_to": "2023-09-30",
        }

        self.assertEqual(en_response.status_code, 200)
        self.assertEqual(en_response.json(), [expected])

        expected["title"] = "Dirección Nacional de Contrataciones Públicas (DNCP)"
        expected["country"] = "Paraguay (ES)"
        expected["language"] = "Español"

        self.assertEqual(es_response.status_code, 200)
        self.assertEqual(es_response.json(), [expected])

        for public, active_job in ((False, True), (True, False), (False, False)):
            with self.subTest(public=public, active_job=active_job):
                collection = models.Collection.objects.create(public=public)
                job1 = collection.job.create(active=active_job)
                job2 = collection.job.create(active=active_job)

                response = Client().get("/es/publications.json")

                collection.delete()
                job1.delete()
                job2.delete()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [expected])
