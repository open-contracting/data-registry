import json
import logging
from datetime import date, datetime
from urllib.parse import urlencode, urljoin

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef, Q
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _

from data_registry.models import Collection, Job
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process
from data_registry.views.serializers import CollectionSerializer
from exporter.util import Export

logger = logging.getLogger(__name__)


def index(request):
    response = render(request, "index.html")

    return response


def search(request):
    results = Collection.objects.all()
    if not request.user.is_authenticated:
        # for unauthenticated user show only public collections with an active job.
        results = results.filter(public=True).filter(
            Exists(Job.objects.filter(collection=OuterRef("pk"), active=True))
        )

    results = results.order_by("country", "title")

    collections = []
    for r in results:
        n = CollectionSerializer.serialize(r)
        n["detail_url"] = reverse("detail", kwargs={"id": r.id})
        collections.append(n)

    return render(request, "search.html", {"collections": collections})


def detail(request, id):
    data = CollectionSerializer.serialize(
        Collection.objects.select_related("license_custom")
        .annotate(issues=ArrayAgg("issue__description", filter=Q(issue__isnull=False)))
        .get(id=id)
    )

    job_id = data.get("active_job", {}).get("id", None)
    years = Export(job_id).years_available()

    return render(
        request,
        "detail.html",
        {
            "data": data,
            "export_years": json.dumps(years),
            "feedback_email": settings.FEEDBACK_EMAIL,
        },
    )


@login_required
def spiders(request):
    url = urljoin(settings.SCRAPYD["url"], "listspiders.json")
    response = requests.get(url, params={"project": settings.SCRAPYD["project"]})

    json = response.json()
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
        subject = f"You have new feedback on the {feedback_collection} dataset"

    mail_text = """
        The following feedback was provided for the {} dataset.

        Type of feedback: {}

        Feedback detail:
        {}
    """.format(
        feedback_collection, feedback_type, feedback_text
    )

    send_mail(
        subject,
        mail_text,
        None,
        [settings.FEEDBACK_EMAIL],
        fail_silently=False,
    )

    return JsonResponse(True, safe=False)


@login_required
def wipe_job(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    Collect(job.collection, job).wipe()
    Process(job).wipe()
    Pelican(job).wipe()
    Exporter(job).wipe()

    return JsonResponse(True, safe=False)


def excel_data(request, job_id, job_range=None):
    job = Job.objects.get(id=job_id)
    export = Export(job_id)

    urls = []
    if job_range is None:
        urls.append((export.directory / "full.jsonl.gz").as_uri())
        job_range = _("All")
    else:
        if job_range == "past-6-months":
            end_date = date.today()
            start_date = date.today() + relativedelta(months=-6)
        if job_range == "last-year":
            end_date = date.today()
            start_date = date.today() + relativedelta(months=-12)
        if "|" in job_range:
            d_from, d_to = job_range.split("|")
            if d_from and d_to:
                start_date = datetime.strptime(d_from, "%Y-%m-%d")
                end_date = datetime.strptime(d_to, "%Y-%m-%d")
                job_range = f"{d_from} - {d_to}"
            elif not d_from:
                start_date = datetime.datetime(1980, 1, 1, 0, 0)
                end_date = datetime.strptime(d_to, "%Y-%m-%d")
                job_range = f"< {d_to}"
            elif not d_to:
                start_date = datetime.strptime(d_from, "%Y-%m-%d")
                end_date = datetime.now()
                job_range = f"> {d_from}"

        while (start_date.year, start_date.month) <= (end_date.year, end_date.month):
            file_path = export.directory / f"{start_date.strftime('%Y_%m')}.jsonl.gz"

            if file_path.exists():
                logger.debug("File %s exists, including in export.", file_path)
                urls.append(file_path.as_uri())
            else:
                logger.debug("File %s does not found. Excluding from export.", file_path)

            start_date = start_date + relativedelta(months=+1)

    body = {
        "urls": urls,
        "country": f"{job.collection.country} {job.collection.title}",
        "period": _(job_range),
        "source": _("OCP Kingfisher Database"),
    }

    headers = {"Accept-Language": f"{get_language()}"}
    response = requests.post(
        urljoin(settings.SPOONBILL_URL, "/api/urls/"),
        body,
        headers=headers,
        auth=(settings.SPOONBILL_API_USERNAME, settings.SPOONBILL_API_PASSWORD),
    )

    logger.info(
        "Sent body request to flatten tool body \n%s headers\n%s\nresponse status code %s.",
        body,
        headers,
        response.status_code,
    )

    if response.status_code > 201 or "id" not in response.json():
        logger.error("Invalid response from spoonbill %s.", response.text)
        return HttpResponse(status=500)

    params = urlencode({"lang": get_language(), "url": response.json()["id"]})
    return redirect(urljoin(settings.SPOONBILL_URL, f"/#/upload-file?{params}"))
