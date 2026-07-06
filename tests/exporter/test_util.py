import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings

from exporter.util import Export


class FilesTests(SimpleTestCase):
    def test_files(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "99"
            job.mkdir()
            for name in ("full.jsonl.gz", "undated.jsonl.gz", "2000.jsonl.gz", "2001.jsonl.gz"):
                (job / name).write_bytes(b"x")

            with override_settings(EXPORTER_DIR=directory, SPOONBILL_EXPORTER_DIR=directory):
                files = Export("99").files

            self.assertEqual(files["jsonl"]["full"], 1)
            self.assertEqual(files["jsonl"]["undated"], 1)
            self.assertEqual(
                sorted(files["jsonl"]["by_year"], key=lambda f: f["year"]),
                [{"year": 2000, "size": 1}, {"year": 2001, "size": 1}],
            )

    def test_files_no_undated(self):
        with tempfile.TemporaryDirectory() as directory:
            job = Path(directory) / "99"
            job.mkdir()
            (job / "full.jsonl.gz").write_bytes(b"x")

            with override_settings(EXPORTER_DIR=directory, SPOONBILL_EXPORTER_DIR=directory):
                files = Export("99").files

            self.assertFalse(files["jsonl"]["undated"])
