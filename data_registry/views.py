import logging
import re
import string
from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import urlencode, urljoin

import requests
from dateutil.relativedelta import relativedelta
from django import urls
from django.conf import settings
from django.db.models import Count, F, Q
from django.db.models.functions import Substr
from django.http.response import FileResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import filesizeformat
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import get_language, get_language_from_request
from django.utils.translation import gettext as _

from data_registry.models import Collection, Job
from data_registry.util import collection_queryset
from exporter.util import Export, TaskStatus

logger = logging.getLogger(__name__)

ALPHABETS = defaultdict(lambda: string.ascii_uppercase)
# https://en.wikipedia.org/wiki/Cyrillic_script_in_Unicode#Basic_Cyrillic_alphabet
ALPHABETS["ru"] = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"

EXPORT_PATTERN = re.compile(r"\A(full|\d{4})\.(jsonl\.gz|csv\.tar\.gz|xlsx)\Z")

FILE_SUFFIXES = {
    "jsonl": "jsonl.gz",
    "xlsx": "xlsx",
    "csv": "csv.tar.gz",
}
ENCODING_FORMATS = {
    # https://docs.aws.amazon.com/sagemaker/latest/dg/cdf-inference.html#cm-batch
    "jsonl": "application/jsonlines",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
}


def index(request):
    return render(request, "index.html")


def search(request):
    """
    Search publications.

    The filter logic is:

    letter AND date_range AND (frequency₁ OR frequency₂ OR …) AND parties_count AND plannings_count AND …
    """

    def without_filter(qs, key="!", *, args=True):
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
        "1M": _("Past month"),
        "6M": _("Past 6 months"),
        "1Y": _("Past year"),
        "5Y": _("Past 5 years"),
    }
    date_limits = {
        "1M": now - timedelta(days=30),
        "6M": now - timedelta(days=180),
        "1Y": now - timedelta(days=365),
        "5Y": now - timedelta(days=1825),
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

    qs = (
        collection_queryset(request)
        .select_related("active_job")
        .annotate(
            letter=Substr(f"country_{language_code}", 1, 1),
            **{count: F(f"active_job__{count}") for count in counts},
        )
    )

    filter_args = []
    filter_kwargs = {}
    exclude = {}
    if "letter" in request.GET:
        filter_kwargs["letter"] = request.GET["letter"]
    if "date_range" in request.GET:
        date_limit = date_limits.get(request.GET["date_range"])
        if date_limit:
            filter_args.append(Q(active_job__date_from__gte=date_limit) | Q(active_job__date_to__gte=date_limit))
    if "update_frequency" in request.GET:
        filter_kwargs["update_frequency__in"] = request.GET.getlist("update_frequency")
    if "region" in request.GET:
        filter_kwargs["region__in"] = request.GET.getlist("region")
    if "counts" in request.GET:
        for count in request.GET.getlist("counts"):
            if count in counts:
                exclude[count] = 0

    facets = {
        "letters": dict.fromkeys(ALPHABETS[language_code], 0),
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
    for row in without_filter(qs, args=False).values("active_job__date_from", "active_job__date_to"):
        facets["date_ranges"][""] += 1
        for value, limit in date_limits.items():
            if (
                row["active_job__date_from"]
                and row["active_job__date_from"] >= limit
                or row["active_job__date_to"]
                and row["active_job__date_to"] >= limit
            ):
                facets["date_ranges"][value] += 1

    for lookup, value in exclude.items():
        qs = qs.exclude(**{lookup: value})
    qs = qs.filter(*filter_args, **filter_kwargs).order_by("country", "title")

    for collection in qs:
        collection.files = Export.get_files(collection.active_job_id)
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
    collection = get_object_or_404(collection_queryset(request).select_related("license_custom"), pk=pk)

    job = collection.active_job
    files = Export.get_files(collection.active_job_id)

    url = request.build_absolute_uri()

    # https://developers.google.com/search/docs/appearance/structured-data/dataset
    dataset = {
        "@context": "https://schema.org/",
        "@type": "Dataset",
        "name": _("OCDS data for %(country)s: %(title)s") % {"country": collection.country, "title": collection.title},
        "description": f"{collection.description}\n\n{collection.description_long}",
        "url": url,
        "image": request.build_absolute_uri(static(f"img/flags/{collection.country_flag}")),
        # Compare to Google Ads campaign.
        "keywords": [
            "public procurement",
            "government contract",
            "tender notices",
            "contract awards",
            "Open Contracting Data Standard",
        ],
        "isAccessibleForFree": True,
        "creator": {
            "@type": "Organization",
            "name": _("Open Contracting Partnership"),
            "url": "https://www.open-contracting.org/",
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "customer service",
                "email": "data@open-contracting.org",
            },
        },
        "includedInDataCatalog": {
            "@type": "DataCatalog",
            "name": _("OCP Data Registry"),
            "description": _("Search for and access datasets by country"),
            "url": request.build_absolute_uri("/"),
        },
        "dateModified": collection.modified.isoformat(),
    }

    if job and (job.date_from or job.date_to):
        dataset["temporalCoverage"] = "/".join(
            date.strftime("%Y-%m-%d") if date else ".." for date in (job.date_from, job.date_to)
        )

    if language := collection.language:
        dataset["inLanguage"] = language

    license_custom = collection.license_custom
    if license_custom and license_custom.url:
        dataset["license"] = license_custom.url
    elif job and job.license:
        dataset["license"] = job.license

    language_code = get_language_from_request(request, check_path=True)
    if language_code != "en":
        dataset["sameAs"] = urls.translate_url(url, "en")

    for file_type, groups in files.items():
        # Segmented files can be added using "hasPart".
        if groups["full"]:
            dataset.setdefault("distribution", [])
            dataset["distribution"].append(
                {
                    "@type": "DataDownload",
                    "encodingFormat": ENCODING_FORMATS[file_type],
                    "contentSize": filesizeformat(groups["full"]),
                    "contentUrl": request.build_absolute_uri(
                        f"{reverse('download', kwargs={'pk': pk})}?name=full.{FILE_SUFFIXES[file_type]}"
                    ),
                    "dateModified": collection.last_retrieved.isoformat(),
                }
            )

    return render(
        request,
        "detail.html",
        {
            "collection": collection,
            "job": job,
            "files": files,
            "dataset": dataset,
            "never": Collection.RetrievalFrequency.NEVER,
        },
    )


def download_export(request, pk):
    name = request.GET.get("name", "")

    # Guard against path traversal.
    if not EXPORT_PATTERN.match(name):
        return HttpResponseBadRequest("The name query string parameter is invalid")

    collection = get_object_or_404(collection_queryset(request), pk=pk)

    export = Export(collection.active_job_id, basename=name)
    if export.status != TaskStatus.COMPLETED:
        return HttpResponseNotFound("File not found")

    return FileResponse(
        export.path.open("rb"),
        as_attachment=True,
        filename=f"{collection.source_id}_{name}",
        # Set Content-Encoding to skip GZipMiddleware. (content_encoding_middleware removes the empty header.)
        # https://docs.djangoproject.com/en/4.2/ref/middleware/#module-django.middleware.gzip
        headers={"Content-Encoding": ""},
    )


def publications_api(request):
    publications = (
        collection_queryset(request)
        .select_related("active_job")
        .values(
            # Identification
            "id",
            "title",
            # Spatial coverage
            "country",
            "region",
            # Language
            "language",
            # Accrual periodicity
            "update_frequency",
            # Provenance
            "source_url",
            # Job logic
            "source_id",
            "retrieval_frequency",
            "last_retrieved",
            "frozen",
        )
        .annotate(date_from=F("active_job__date_from"), date_to=F("active_job__date_to"))
    )
    return JsonResponse(
        list(publications),
        safe=False,  # safe=True requires dict
        json_dumps_params={"ensure_ascii": False, "separators": (",", ":")},
        content_type="application/json; charset=utf-8",  # some browsers assume incorrect charset
        headers={"Access-Control-Allow-Origin": "*"},
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
        timeout=10,
    )

    logger.info(
        "Sent body request to flatten tool body \n%s headers\n%s\nresponse status code %s.",
        body,
        headers,
        response.status_code,
    )

    if response.status_code > requests.codes.created or "id" not in response.json():
        logger.error("Invalid response from spoonbill %s.", response.text)
        return HttpResponse(status=requests.codes.internal_server_error)

    params = urlencode({"lang": language, "url": response.json()["id"]})
    return redirect(urljoin(settings.SPOONBILL_URL, f"/#/upload-file?{params}"))
