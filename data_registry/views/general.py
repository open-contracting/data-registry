import json
import logging
import os
from datetime import date, datetime

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import send_mail
from django.db.models.expressions import Exists, OuterRef
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from data_registry.cbom.task.exporter import Exporter
from data_registry.cbom.task.pelican import Pelican
from data_registry.cbom.task.process import Process
from data_registry.cbom.task.scrape import Scrape
from data_registry.models import Collection, Job
from data_registry.views.serializers import CollectionSerializer

logger = logging.getLogger(__name__)


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
def wipe_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    Scrape(job.collection, job).wipe()
    Process(job).wipe()
    Pelican(job).wipe()
    Exporter(job).wipe()

    return JsonResponse(True, safe=False)


def excel_data(request, job_id, job_range):
    job = Job.objects.get(id=job_id)

    spider = job.collection.source_id

    dump_dir = "{}/{}/{}".format(settings.EXPORTER_DIR, spider, job_id)

    urls = []
    if job_range == "null":
        urls = "file://{}/full.jsonl.gz".format(dump_dir)
        job_range = _("All data")
    else:
        if job_range == "past-6-months":
            end_date = date.today()
            start_date = (date.today() + relativedelta(months=-6))
        if job_range == "last-year":
            end_date = date.today()
            start_date = (date.today() + relativedelta(months=-12))
        if "|" in job_range:
            dates = job_range.split("|")
            start_date = datetime.strptime(dates[0], "%Y-%m-%d")
            end_date = datetime.strptime(dates[1], "%Y-%m-%d")
            job_range = "{} - {}".format(dates[0], dates[1])

        while "{}{}".format(start_date.year, start_date.month) <= "{}{}".format(end_date.year, end_date.month):
            file_path = "{}/{}.jsonl.gz".format(dump_dir, start_date.strftime("%Y_%m"))

            if os.path.isfile(file_path):
                logger.debug("File {} exists, including in export.".format(file_path))
                urls.append("file://{}".format(file_path))
            else:
                logger.debug("File {} does not found. Excluding from in export.".format(file_path))

            start_date = start_date + relativedelta(months=+1)

    body = {
        "urls": urls,
        "country": "{} {}".format(job.collection.country, job.collection.title),
        "period": _(job_range),
        "source": _("OCP Kingfisher Database")
    }

    headers = {"Accept-Language": "{}".format(get_language())}
    response = requests.post("{}/api/urls/".format(settings.FLATTEN_URL), body, headers=headers)

    logger.error("Sent body request to flatten tool body \n{} headers\n{}\nLanguageResponse status code {}.".format(
        body, headers, response.status_code))

    if response.status_code > 201 or "id" not in response.json():
        logger.error("Invalid response from spoonbill {}.".format(response.text))
        return HttpResponse(status=500)

    return redirect("{}/#/upload-file?&url={}".format(settings.FLATTEN_URL, response.json()["id"]))
