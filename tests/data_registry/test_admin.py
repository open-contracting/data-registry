from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from data_registry.models import Collection, Job
from data_registry.util import CHANGELIST

URL = reverse(CHANGELIST.format(content_type=ContentType.objects.get_for_model(Job)))


class AdminTests(TestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("Test")

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_job_out_of_date(self):
        response = self.client.post(URL, {"action": "create_job", "_selected_action": 1})

        self.assertEqual(
            [(message.level, message.message) for message in messages.get_messages(response.wsgi_request)],
            [
                (messages.SUCCESS, "Created 0 jobs."),
                (messages.WARNING, "1 publication either has an incomplete job or will be scheduled shortly."),
            ],
        )
        self.assertEqual(Collection.objects.get(pk=1).job_set.count(), 0)

    def test_create_job_incomplete(self):
        collection = Collection.objects.get(pk=2)
        job = Job.objects.get(pk=1)
        job.start = timezone.now()
        job.save()

        self.assertEqual(collection.job_set.count(), 1)

        data = {"action": "create_job", "_selected_action": 2}
        response = self.client.post(URL, data)

        self.assertEqual(
            [(message.level, message.message) for message in messages.get_messages(response.wsgi_request)],
            [(messages.SUCCESS, "Created 1 job.")],
        )
        self.assertEqual(collection.job_set.count(), 2)

        self.client.cookies.pop("messages")
        response = self.client.post(URL, data)

        self.assertEqual(
            [(message.level, message.message) for message in messages.get_messages(response.wsgi_request)],
            [
                (messages.SUCCESS, "Created 0 jobs."),
                (messages.WARNING, "1 publication either has an incomplete job or will be scheduled shortly."),
            ],
        )
        self.assertEqual(collection.job_set.count(), 2)
