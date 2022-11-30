from django.test import SimpleTestCase

from data_registry.templatetags.registry import humanfilesize


class UtilTests(SimpleTestCase):
    def test_human_file_size(self):
        for size, expected in (
            (1, "< 1 MB"),
            (949999, "< 1 MB"),
            (950000, "< 1 MB"),
            (999999, "< 1 MB"),
            (1499999, "1 MB"),
            (1500000, "2 MB"),
            (1234567890, "1,235 MB"),
        ):
            with self.subTest(size=size):
                self.assertEqual(humanfilesize(size), expected)
