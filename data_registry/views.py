import logging
import re
from datetime import date, timedelta

from django import urls
from django.conf import settings
from django.db.models import Count, F, Q
from django.http.response import FileResponse, HttpResponseBadRequest, HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import filesizeformat
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import get_language_from_request
from django.utils.translation import gettext as _

from data_registry.models import Collection
from data_registry.util import collection_queryset
from exporter.util import Export, TaskStatus

logger = logging.getLogger(__name__)

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

    country AND date_range AND (frequency₁ OR frequency₂ OR …) AND parties_count AND plannings_count AND …
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
    country_field = f"country_{language_code}"

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
            **{count: F(f"active_job__{count}") for count in counts},
        )
    )

    filter_args = []
    filter_kwargs = {}
    exclude = {}
    if "country" in request.GET:
        filter_kwargs["country"] = request.GET["country"]
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
        "countries": dict.fromkeys(
            collection_queryset(request).values_list(country_field, flat=True).distinct().order_by(country_field), 0
        ),
        "date_ranges": dict.fromkeys(date_ranges, 0),
        "frequencies": dict.fromkeys(Collection.UpdateFrequency.values, 0),
        "regions": dict.fromkeys(Collection.Region.values, 0),
        "counts": dict.fromkeys(counts, 0),
    }
    for value, n in facet_counts(qs, "country"):
        facets["countries"][value] = n
    for value, n in facet_counts(qs, "update_frequency"):
        facets["frequencies"][value] = n
    for value, n in facet_counts(qs, "region"):
        facets["regions"][value] = n
    for row in without_filter(qs, args=False).values("active_job__date_from", "active_job__date_to"):
        facets["date_ranges"][""] += 1
        for value, limit in date_limits.items():
            if (row["active_job__date_from"] and row["active_job__date_from"] >= limit) or (
                row["active_job__date_to"] and row["active_job__date_to"] >= limit
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
    collection = get_object_or_404(
        collection_queryset(request).select_related("active_job", "license_custom"),
        pk=pk,
    )

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

    date_from = collection.date_from or getattr(job, "date_from", None)
    date_to = collection.date_to or getattr(job, "date_to", None)
    if date_from and date_to:
        dataset["temporalCoverage"] = f"{date_from.strftime('%Y-%m-%d')}/{date_to.strftime('%Y-%m-%d')}"

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

    if settings.DOWNLOADS_URL:
        return redirect(f"{settings.DOWNLOADS_URL}/downloads/{collection.source_id}/{collection.active_job_id}/{name}")

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
        .annotate(
            date_from=F("active_job__date_from"), date_to=F("active_job__date_to"), coverage=F("active_job__coverage")
        )
    )
    return JsonResponse(
        list(publications),
        safe=False,  # safe=True requires dict
        json_dumps_params={"ensure_ascii": False, "separators": (",", ":")},
        content_type="application/json; charset=utf-8",  # some browsers assume incorrect charset
        headers={"Access-Control-Allow-Origin": "*"},
    )
