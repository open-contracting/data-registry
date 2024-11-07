import datetime
import os.path
from unittest.mock import PropertyMock, patch

from django.test import Client, TestCase, override_settings

from data_registry import models


@override_settings(
    STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
    EXPORTER_DIR=os.path.join("tests", "fixtures"),
)
class ViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.collection1 = models.Collection.objects.create(
            # Identification
            title="Ignore",
            title_en="National Directorate of Public Procurement (DNCP)",
            title_es="Dirección Nacional de Contrataciones Públicas (DNCP)",
            # Spatial coverage
            country="Ignore",
            country_en="Paraguay (EN)",
            country_es="Paraguay (ES)",
            region=models.Collection.Region.LAC,
            # Language
            language="Ignore",
            language_en="Spanish",
            language_es="Español",
            # Provenance
            source_url="https://contrataciones.gov.py/datos/api/v3/doc/",
            # Job logic
            source_id="paraguay_dncp_records",
            retrieval_frequency=models.Collection.RetrievalFrequency.MONTHLY,
            last_retrieved=datetime.date(2001, 2, 3),
            # Visibility logic
            public=True,
        )
        cls.job = cls.collection1.active_job = cls.collection1.job_set.create(
            id=99,  # to match tests/fixtures directory
            date_from=datetime.date(2010, 2, 1),
            date_to=datetime.date(2023, 9, 30),
        )
        cls.collection1.save()

        cls.collection2 = models.Collection.objects.create(
            # Identification
            title="Another",
            title_en="Title",
            title_es="Título",
            # Spatial coverage
            country="Another",
            country_en="Canada (EN)",
            country_es="Canada (ES)",
            region=models.Collection.Region.LAC,
            # Language
            language="Another",
            language_en="English",
            language_es="Inglés",
            # Provenance
            source_url="https://example.com",
            # Job logic
            source_id="canada_buyandsell",
            retrieval_frequency=models.Collection.RetrievalFrequency.MONTHLY,
            last_retrieved=datetime.date(2001, 2, 3),
            # Visibility logic
            public=True,
        )
        cls.collection2.active_job = cls.collection2.job_set.create(
            date_from=datetime.date(2010, 2, 1),
            date_to=None,
        )
        cls.collection2.save()

        cls.collection_no_files = models.Collection.objects.create(title="Test", source_id="test", public=True)
        cls.collection_no_files.active_job = cls.collection_no_files.job_set.create()
        cls.collection_no_files.save()

    def test_search(self):
        # letter, update_frequency, region, dates, results
        with self.assertNumQueries(5):
            response = Client().get("/en/search/")

            self.assertTemplateUsed("search.html")
            self.assertContains(response, f'"/en/publication/{self.collection1.id}"')
            self.assertContains(response, f'"/en/publication/{self.collection2.id}"')

    @patch("exporter.util.Export.get_files")
    def test_detail(self, get_files):
        get_files.return_value = {"jsonl": {"full": 123, "by_year": [{"year": 2022, "size": 1}]}}
        url = f"/en/publication/{self.collection1.id}/download?name=2022.jsonl.gz"

        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection1.id}")

            self.assertTemplateUsed("detail.html")
            self.assertContains(
                response, f"""<a href="{url}" rel="nofollow" data-event="jsonl.gz year" download>2022</a>""", html=True
            )

    def test_detail_missing_date(self):
        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection2.id}")

            self.assertTemplateUsed("detail.html")
            self.assertContains(response, '"temporalCoverage": "2010-02-01/..",')

    def test_collection_not_found(self):
        with self.assertNumQueries(1):
            response = Client().get("/en/publication/10/download?name=2000.jsonl.gz")

            self.assertEqual(response.status_code, 404)

    def test_download_export_invalid_suffix(self):
        with self.assertNumQueries(0):
            response = Client().get(f"/en/publication/{self.collection1.id}/download?name=invalid")

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content, b"The name query string parameter is invalid")

    def test_download_export_empty_parameter(self):
        with self.assertNumQueries(0):
            response = Client().get(f"/en/publication/{self.collection1.id}/download?name=")

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content, b"The name query string parameter is invalid")

    def test_download_export_waiting(self):
        with self.assertNumQueries(1):
            response = Client().get(f"/en/publication/{self.collection_no_files.id}/download?name=2000.jsonl.gz")

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content, b"File not found")

    @patch("exporter.util.Export.lockfile", new_callable=PropertyMock)
    def test_download_export_running(self, exists):
        with self.assertNumQueries(1):
            response = Client().get(f"/en/publication/{self.collection1.id}/download?name=2000.jsonl.gz")

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content, b"File not found")

    def test_download_export_completed(self):
        for suffix, content_type in (
            ("jsonl.gz", "application/gzip"),
            ("csv.tar.gz", "application/gzip"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ):
            with self.subTest(suffix=suffix), self.assertNumQueries(1):
                response = Client().get(
                    f"/en/publication/{self.collection1.id}/download?name=2000.{suffix}",
                    HTTP_ACCEPT_ENCODING="gzip",
                )

                response.headers.pop("Content-Length")

                self.assertEqual(response.status_code, 200)
                self.assertDictEqual(
                    dict(response.headers),
                    {
                        "Content-Disposition": f'attachment; filename="paraguay_dncp_records_2000.{suffix}"',
                        "Content-Language": "en",
                        "Content-Type": content_type,
                        "Cross-Origin-Opener-Policy": "same-origin",
                        "Referrer-Policy": "same-origin",
                        "Vary": "Cookie",
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                    },
                )
                with open(os.path.join("tests", "fixtures", "99", f"2000.{suffix}"), "rb") as f:
                    self.assertEqual(b"".join(response.streaming_content), f.read())

    @override_settings(SCRAPYD={"url": "http://127.0.0.1", "project": "kingfisher"})
    def test_publications_api(self):
        en_response = Client().get("/en/publications.json")
        es_response = Client().get("/es/publications.json")

        expected = [
            {
                "id": self.collection1.id,
                "title": "National Directorate of Public Procurement (DNCP)",
                "country": "Paraguay (EN)",
                "region": "LAC",
                "language": "Spanish",
                "update_frequency": "UNKNOWN",
                "source_url": "https://contrataciones.gov.py/datos/api/v3/doc/",
                "source_id": "paraguay_dncp_records",
                "retrieval_frequency": "MONTHLY",
                "last_retrieved": "2001-02-03",
                "frozen": False,
                "date_from": "2010-02-01",
                "date_to": "2023-09-30",
            },
            {
                "id": self.collection2.id,
                "title": "Title",
                "country": "Canada (EN)",
                "region": "LAC",
                "language": "English",
                "update_frequency": "UNKNOWN",
                "source_url": "https://example.com",
                "source_id": "canada_buyandsell",
                "retrieval_frequency": "MONTHLY",
                "last_retrieved": "2001-02-03",
                "frozen": False,
                "date_from": "2010-02-01",
                "date_to": None,
            },
            {
                "id": self.collection_no_files.id,
                "title": "Test",
                "country": "",
                "region": "",
                "language": "",
                "update_frequency": "UNKNOWN",
                "source_url": "",
                "source_id": "test",
                "retrieval_frequency": "",
                "last_retrieved": None,
                "frozen": False,
                "date_from": None,
                "date_to": None,
            },
        ]

        self.assertEqual(en_response.status_code, 200)
        self.assertEqual(en_response.json(), expected)
        self.assertNotIn(b": ", en_response.content)  # separators

        expected[0]["title"] = "Dirección Nacional de Contrataciones Públicas (DNCP)"
        expected[0]["country"] = "Paraguay (ES)"
        expected[0]["language"] = "Español"
        expected[1]["title"] = "Título"
        expected[1]["country"] = "Canada (ES)"
        expected[1]["language"] = "Inglés"

        self.assertEqual(es_response.status_code, 200)
        self.assertEqual(es_response.json(), expected)
        self.assertNotIn(b"\\u", es_response.content)  # ensure_ascii

        for public, active_job in ((False, True), (True, False), (False, False)):
            with self.subTest(public=public, active_job=active_job):
                collection = models.Collection.objects.create(public=public)
                job = collection.job_set.create()
                if active_job:
                    collection.active_job = job
                    collection.save()

                response = Client().get("/es/publications.json")

                collection.delete()
                job.delete()

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), expected)
