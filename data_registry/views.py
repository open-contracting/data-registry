import logging
import re
import string
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

import requests
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Substr
from django.http.response import FileResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import get_language, get_language_from_request
from django.utils.translation import gettext as _

from data_registry.models import Collection, Job
from data_registry.util import collection_queryset
from exporter.util import Export, TaskStatus

logger = logging.getLogger(__name__)

alphabets = defaultdict(lambda: string.ascii_uppercase)
# https://en.wikipedia.org/wiki/Cyrillic_script_in_Unicode#Basic_Cyrillic_alphabet
alphabets["ru"] = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
EXPORT_PATTERN = re.compile(r"\A(full|\d{4})\.(jsonl\.gz|csv\.tar\.gz|xlsx)\Z")


def index(request):
    return render(request, "index.html")


def search(request):
    """
    The filter logic is:

    letter AND date_range AND (frequency₁ OR frequency₂ OR …) AND parties_count AND plannings_count AND …
    """

    def without_filter(qs, key="!", args=True):
        for lookup, value in exclude.items():
            if not lookup.startswith(key):
                qs = qs.exclude(**{lookup: value})
        if args:
            qs = qs.filter(*filter_args)
        return qs.filter(**{k: v for k, v in filter_kwargs.items() if not k.startswith(key)})

    def facet_counts(qs, key):
        return without_filter(qs, key).exclude(**{key: ""}).values(key).annotate(n=Count("pk")).values_list(key, "n")

    now = date.today()
    language_code = get_language_from_request(request, check_path=True)

    date_ranges = {
        "": _("All"),
        "1Y": _("Past year"),
        "6M": _("Past 6 months"),
    }

    date_limits = {
        "1Y": now - timedelta(days=365),
        "6M": now - timedelta(days=183),
    }

    counts = {
        "parties_count": _("Parties data"),
        "plannings_count": _("Plannings data"),
        "tenders_count": _("Tenders data"),
        "awards_count": _("Awards data"),
        "contracts_count": _("Contracts data"),
        "documents_count": _("Documents data"),
        "milestones_count": _("Milestones data"),
        "amendments_count": _("Amendments data"),
    }

    # https://docs.djangoproject.com/en/4.2/ref/models/expressions/#subquery-expressions
    active_job = Job.objects.active().filter(collection=OuterRef("pk"))[:1]
    qs = collection_queryset(request).annotate(
        job_id=Subquery(active_job.values("pk")),
        # Display
        date_from=Subquery(active_job.values("date_from")),
        date_to=Subquery(active_job.values("date_to")),
        # Filter
        letter=Substr(f"country_{language_code}", 1, 1),
        **{count: Subquery(active_job.values(count)) for count in counts},
    )

    filter_args = []
    filter_kwargs = {}
    exclude = {}
    if "letter" in request.GET:
        filter_kwargs["letter"] = request.GET["letter"]
    if "date_range" in request.GET:
        date_limit = date_limits.get(request.GET["date_range"])
        if date_limit:
            filter_args.append(Q(date_from__gte=date_limit) | Q(date_to__gte=date_limit))
    if "update_frequency" in request.GET:
        filter_kwargs["update_frequency__in"] = request.GET.getlist("update_frequency")
    if "region" in request.GET:
        filter_kwargs["region__in"] = request.GET.getlist("region")
    if "counts" in request.GET:
        for count in request.GET.getlist("counts"):
            exclude[count] = 0

    facets = {
        "letters": dict.fromkeys(alphabets[language_code], 0),
        "date_ranges": dict.fromkeys(date_ranges, 0),
        "frequencies": dict.fromkeys(Collection.UpdateFrequency.values, 0),
        "regions": dict.fromkeys(Collection.Region.values, 0),
        "counts": dict.fromkeys(counts, 0),
    }
    for value, n in facet_counts(qs, "letter"):
        facets["letters"][value] = n
    for value, n in facet_counts(qs, "update_frequency"):
        facets["frequencies"][value] = n
    for value, n in facet_counts(qs, "region"):
        facets["regions"][value] = n
    for row in without_filter(qs, args=False).values("date_from", "date_to"):
        facets["date_ranges"][""] += 1
        for value, limit in date_limits.items():
            if row["date_from"] and row["date_from"] >= limit or row["date_to"] and row["date_to"] >= limit:
                facets["date_ranges"][value] += 1

    for lookup, value in exclude.items():
        qs = qs.exclude(**{lookup: value})
    qs = qs.filter(*filter_args, **filter_kwargs).order_by("country", "title")

    for collection in qs:
        collection.files = Export.get_files(collection.job_id)
        for value in counts:
            if getattr(collection, value):
                facets["counts"][value] += 1

    context = {
        "collections": qs,
        "facets": facets,
        "date_ranges": date_ranges,
        "frequencies": Collection.UpdateFrequency.choices,
        "regions": Collection.Region.choices,
        "counts": counts,
        "never": Collection.RetrievalFrequency.NEVER,
    }
    return render(request, "search.html", context)


def detail(request, pk):
    collection = get_object_or_404(
        collection_queryset(request)
        .select_related("license_custom")
        .annotate(issues=ArrayAgg("issue__description", filter=Q(issue__isnull=False), default=None)),
        pk=pk,
    )

    job = collection.active_job
    files = Export.get_files(job and job.id)

    return render(
        request,
        "detail.html",
        {"collection": collection, "job": job, "files": files, "never": Collection.RetrievalFrequency.NEVER},
    )


def download_export(request, pk):
    name = request.GET.get("name", "")

    # Guard against path traversal.
    if not EXPORT_PATTERN.match(name):
        return HttpResponseBadRequest("The name query string parameter is invalid")

    collection = get_object_or_404(collection_queryset(request), pk=pk)
    active_job = get_object_or_404(collection.job_set.active())

    export = Export(active_job.id, basename=name)
    if export.status != TaskStatus.COMPLETED:
        return HttpResponseNotFound("File not found")

    return FileResponse(
        export.path.open("rb"),
        as_attachment=True,
        filename=f"{collection.source_id}_{name}",
        # Set Content-Encoding to skip GZipMiddleware. (ContentEncodingMiddleware removes the empty header.)
        # https://docs.djangoproject.com/en/4.2/ref/middleware/#module-django.middleware.gzip
        headers={"Content-Encoding": ""},
    )


def publications_api(request):
    active_job = Job.objects.active().filter(collection=OuterRef("pk"))[:1]
    publications = (
        collection_queryset(request)
        .values(
            # Identification
            "id",
            "title",
            "country",
            # Accrual periodicity
            "last_retrieved",
            "retrieval_frequency",
            "update_frequency",
            "frozen",
            # Provenance
            "source_id",
            "source_url",
            # Other details
            "region",
            "language",
        )
        .annotate(
            date_from=Subquery(active_job.values("date_from")),
            date_to=Subquery(active_job.values("date_to")),
        )
    )
    return JsonResponse(
        list(publications), safe=False, json_dumps_params={"ensure_ascii": False, "separators": (",", ":")}
    )


def excel_data(request, job_id, job_range=None):
    job = Job.objects.get(pk=job_id)
    export = Export(job_id)

    urls = []
    if job_range is None:
        urls.append((export.spoonbill_directory / "full.jsonl.gz").as_uri())
        job_range = _("All")
    else:
        if job_range == "6M":
            end_date = date.today()
            start_date = date.today() + relativedelta(months=-6)
        if job_range == "1Y":
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
            file_path = export.spoonbill_directory / f"{start_date.strftime('%Y_%m')}.jsonl.gz"

            if file_path.exists():
                logger.debug("File %s exists, including in export.", file_path)
                urls.append(file_path.as_uri())
            else:
                logger.debug("File %s does not found. Excluding from export.", file_path)

            start_date = start_date + relativedelta(months=+1)

    language = get_language()

    body = {
        "urls": urls,
        "country": f"{job.collection.country} {job.collection.title}",
        "period": _(job_range),
        "source": _("OCP Kingfisher Database"),
    }

    headers = {"Accept-Language": f"{language}"}
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

    params = urlencode({"lang": language, "url": response.json()["id"]})
    return redirect(urljoin(settings.SPOONBILL_URL, f"/#/upload-file?{params}"))
