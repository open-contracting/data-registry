import json

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import send_mail
from django.db.models.expressions import Exists, OuterRef
from django.db.models.query_utils import Q
from django.http.response import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from markdownx.utils import markdownify

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

    collections = []
    for r in results:
        n = CollectionSerializer.serialize(r)
        n["detail_url"] = reverse("detail", kwargs={"id": r.id})
        collections.append(n)

    return render(request, 'search.html', {"collections": collections})


def detail(request, id):
    data = CollectionSerializer.serialize(
        Collection.objects
        .annotate(issues=ArrayAgg("issue__description", filter=Q(issue__isnull=False)))
        .get(id=id)
    )

    markdown_fields = ["additional_data", "description_long", "summary", "issues"]
    for f in markdown_fields:
        if f in data and data[f] is not None:
            if type(data[f]) == list:
                data[f] = [markdownify(n) for n in data[f]]
            else:
                data[f] = markdownify(data[f])

    return render(request, 'detail.html', {'data': data})


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

    send_mail(
        f'Data registry feedback - {feedback_type}',
        feedback_text,
        'feedback@data-registry',
        [settings.FEEDBACK_EMAIL],
        fail_silently=False,
    )

    return JsonResponse(True, safe=False)
