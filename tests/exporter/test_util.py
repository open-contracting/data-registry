from unittest.mock import patch

from django.test import SimpleTestCase

from exporter.util import Export


class UtilTests(SimpleTestCase):
    def test_human_file_size(self):
        export = Export()
        for size, expected in (
            (1, "0.1 MB"),
            (949999, "0.9 MB"),
            (950000, "1 MB"),
            (1499999, "1 MB"),
            (1500000, "2 MB"),
            (1234567890, "1,235 MB"),
        ):
            with self.subTest(size=size):
                with patch("os.path.getsize") as getsize:
                    getsize.return_value = size
                    self.assertEqual(export.human_file_size(size), expected)
