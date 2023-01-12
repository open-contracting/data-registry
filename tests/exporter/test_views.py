import os.path
from unittest.mock import PropertyMock, patch

from django.test import Client, TestCase, override_settings


@override_settings(EXPORTER_DIR=os.path.join("tests", "fixtures"))
class ViewsTests(TestCase):
    def test_download_export_invalid_suffix(self):
        response = Client().get("/api/download_export?suffix=invalid")

        self.assertNumQueries(0)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Suffix not recognized")

    def test_download_export_empty_parameter(self):
        for parameter in ("job_id", "year"):
            with self.subTest(parameter=parameter):
                response = Client().get(f"/api/download_export?suffix=jsonl.gz&{parameter}=")

                self.assertNumQueries(0)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.content, b"File not found")

    def test_download_export_waiting(self):
        response = Client().get("/api/download_export?suffix=jsonl.gz&year=2000&job_id=0")

        self.assertNumQueries(0)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"File not found")

    @patch("exporter.util.Export.lockfile", new_callable=PropertyMock)
    def test_download_export_running(self, exists):
        response = Client().get("/api/download_export?suffix=jsonl.gz&year=2000&job_id=1")

        self.assertNumQueries(0)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content, b"File not found")

    def test_download_export_completed(self):
        for suffix, content_type in (
            ("jsonl.gz", "application/gzip"),
            ("csv.tar.gz", "application/gzip"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ):
            with self.subTest(suffix=suffix):
                response = Client().get(
                    f"/api/download_export?suffix={suffix}&year=2000&job_id=1&spider=abc", HTTP_ACCEPT_ENCODING="gzip"
                )

                self.assertNumQueries(0)
                self.assertEqual(response.status_code, 200)
                self.assertDictEqual(
                    dict(response.headers),
                    {
                        "Content-Disposition": f'attachment; filename="abc_2000.{suffix}"',
                        "Content-Language": "en",
                        "Content-Type": content_type,
                        "Referrer-Policy": "same-origin",
                        "Vary": "Accept-Language",
                        "X-Content-Type-Options": "nosniff",
                        "X-Frame-Options": "DENY",
                    },
                )
                with open(os.path.join("tests", "fixtures", "1", f"2000.{suffix}"), "rb") as f:
                    self.assertEqual(b"".join(response.streaming_content), f.read())
