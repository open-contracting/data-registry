import json

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import send_mail
from django.db.models.expressions import Exists, OuterRef
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from data_registry.cbom.task.exporter import Exporter
from data_registry.cbom.task.pelican import Pelican
from data_registry.cbom.task.process import Process
from data_registry.cbom.task.scrape import Scrape
from data_registry.models import Collection, Job
from data_registry.views.serializers import CollectionSerializer


def index(request):
    response = render(request, 'index.html')

    return response


def search(request):
    results = Collection.objects.all()
    if not request.user.is_authenticated:
        # for unauthenticated user show only public collections with an active job.
        results = results\
            .filter(public=True)\
            .filter(Exists(Job.objects.filter(collection=OuterRef('pk'), active=True)))

    results = results.order_by('country', 'title')

    collections = []
    for r in results:
        n = CollectionSerializer.serialize(r)
        n["detail_url"] = reverse("detail", kwargs={"id": r.id})
        collections.append(n)

    return render(request, 'search.html', {"collections": collections})


def detail(request, id):
    data = CollectionSerializer.serialize(
        Collection.objects
        .select_related("license_custom")
        .annotate(issues=ArrayAgg("issue__description", filter=Q(issue__isnull=False)))
        .get(id=id)
    )

    resp = requests.post(
        f"{settings.EXPORTER_HOST}api/export_years",
        json={
            "job_id": data.get("active_job", {}).get("id", None),
            "spider": data.get("source_id")
        }
    )

    years = resp.json().get("data")

    return render(
        request,
        'detail.html',
        {
            'data': data,
            'exporter_host': settings.EXPORTER_HOST,
            'export_years': json.dumps(years),
            'feedback_email': settings.FEEDBACK_EMAIL
        }
    )


@login_required
def spiders(request):
    resp = requests.get(
        settings.SCRAPY_HOST + "listspiders.json",
        params={
            "project": settings.SCRAPY_PROJECT
        }
    )

    json = resp.json()
    if json.get("status") == "error":
        raise JsonResponse(json, status=503, safe=False)

    return JsonResponse(json.get("spiders"), safe=False)


def send_feedback(request):
    body = json.loads(request.body.decode("utf8"))
    feedback_type = body.get("type")
    feedback_text = body.get("text")
    feedback_collection = body.get("collection")

    subject = f"Data registry feedback - {feedback_type}"
    if feedback_collection:
        subject = f'You have new feedback on the {feedback_collection} dataset'

    mail_text = """
        The following feedback was provided for the {} dataset.

        Type of feedback: {}

        Feedback detail:
        {}
    """.format(feedback_collection, feedback_type, feedback_text)

    send_mail(
        subject,
        mail_text,
        'noreply@noreply.open-contracting.org',
        [settings.FEEDBACK_EMAIL],
        fail_silently=False,
    )

    return JsonResponse(True, safe=False)


@login_required
def wipe_job(job_id):
    job = get_object_or_404(Job, pk=job_id)

    Scrape(job.collection, job).wipe()
    Process(job).wipe()
    Pelican(job).wipe()
    Exporter(job).wipe()

    job.delete()
