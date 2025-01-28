from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from data_registry.models import Collection, Job


class AdminTests(TestCase):
    fixtures = ["tests/fixtures/fixtures.json"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("Test")

    def test_create_job(self):
        content_type = ContentType.objects.get_for_model(Collection)
        collection = Collection.objects.get(pk=1)
        # No jobs
        data = {
            "action": "create_job",
            "_selected_action": collection.pk,
        }
        self.client.force_login(self.user)
        response = self.client.post(reverse(f"admin:{content_type.app_label}_{content_type.model}_changelist"), data)
        self.assertEqual(
            str(next(iter(get_messages(response.wsgi_request)))),
            "Created 0 jobs. 1 publications either have incomplete jobs or will be scheduled shortly.",
        )
        self.assertEqual(collection.job_set.count(), 0)

        # Out of date job
        self.client.cookies.pop("messages")
        out_of_date_collection = Collection.objects.get(pk=2)
        out_of_date_job = Job.objects.get(pk=1)
        out_of_date_job.start = timezone.now()
        out_of_date_job.save()
        data["_selected_action"] = out_of_date_collection.pk
        response = self.client.post(reverse(f"admin:{content_type.app_label}_{content_type.model}_changelist"), data)
        self.assertEqual(str(next(iter(get_messages(response.wsgi_request)))), "Created 1 jobs.")
        self.assertEqual(out_of_date_collection.job_set.count(), 2)

        # Incomplete job
        self.client.cookies.pop("messages")
        response = self.client.post(reverse(f"admin:{content_type.app_label}_{content_type.model}_changelist"), data)
        self.assertEqual(
            str(next(iter(get_messages(response.wsgi_request)))),
            "Created 0 jobs. 1 publications either have incomplete jobs or will be scheduled shortly.",
        )
        self.assertEqual(out_of_date_collection.job_set.count(), 2)
