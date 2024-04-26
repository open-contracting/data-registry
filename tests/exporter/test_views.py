import os.path
from unittest.mock import PropertyMock, patch

from django.test import Client, TestCase, override_settings

from data_registry.models import Collection


@override_settings(EXPORTER_DIR=os.path.join("tests", "fixtures"))
class ViewsTests(TestCase):
    @classmethod
    def setUp(cls):
        cls.collection = Collection.objects.create(
            id=2,
            title="Dirección Nacional de Contrataciones Públicas (DNCP)",
            source_id="abc",
            public=True,
        )
        cls.job = cls.collection.job_set.create(
            active=True,
            id=2,
        )
        cls.collection_no_job = Collection.objects.create(
            id=3,
            title="Test",
            source_id="abc",
            public=True,
        )
        cls.collection_no_job.job_set.create(
            active=True,
            id=4,
        )

    def test_collection_not_found(self):
        with self.assertNumQueries(1):
            response = Client().get("/en/publication/10/download?name=2000.jsonl.gz")

        self.assertEqual(response.status_code, 404)

    def test_download_export_invalid_suffix(self):
        with self.assertNumQueries(0):
            response = Client().get(f"/en/publication/{self.collection.id}/download?name=invalid")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"The name query string parameter is invalid")

    def test_download_export_empty_parameter(self):
        with self.assertNumQueries(0):
            response = Client().get(f"/en/publication/{self.collection.id}/download?name=")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"The name query string parameter is invalid")

    def test_download_export_waiting(self):
        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection_no_job.id}/download?name=2000.jsonl.gz")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"File not found")

    @patch("exporter.util.Export.lockfile", new_callable=PropertyMock)
    def test_download_export_running(self, exists):
        with self.assertNumQueries(2):
            response = Client().get(f"/en/publication/{self.collection.id}/download?name=2000.jsonl.gz")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"File not found")

    def test_download_export_completed(self):
        for suffix, content_type in (
            ("jsonl.gz", "application/gzip"),
            ("csv.tar.gz", "application/gzip"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ):
            with self.subTest(suffix=suffix):
                with self.assertNumQueries(2):
                    response = Client().get(
                        f"/en/publication/{self.collection.id}/download?name=2000.{suffix}",
                        HTTP_ACCEPT_ENCODING="gzip",
                    )
                self.assertEqual(response.status_code, 200)
                response.headers.pop("Content-Length")
                self.assertDictEqual(
                    dict(response.headers),
                    {
                        "Content-Disposition": f'attachment; filename="abc_2000.{suffix}"',
                        "Content-Language": "en",
                        "Content-Type": content_type,
                        "Cross-Origin-Opener-Policy": "same-origin",
                        "Referrer-Policy": "same-origin",
                        "Vary": "Cookie",
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                    },
                )
                with open(os.path.join("tests", "fixtures", "2", f"2000.{suffix}"), "rb") as f:
                    self.assertEqual(b"".join(response.streaming_content), f.read())
