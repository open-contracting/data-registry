import re

from django.http import FileResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from data_registry.util import collection_queryset
from exporter.util import Export, TaskStatus

EXPORT_PATTERN = re.compile(r"\A(full|\d{4})\.(jsonl\.gz|csv\.tar\.gz|xlsx)\Z")


def download_export(request, id):
    """
    Returns an exported file as a FileResponse object.
    """
    name = request.GET.get("name")

    # Guard against path traversal.
    if not EXPORT_PATTERN.match(name):
        return HttpResponseBadRequest("The name query string parameter is invalid")

    collection = get_object_or_404(collection_queryset(request), id=id)

    active_job = collection.job.filter(active=True).first()
    if not active_job:
        return HttpResponseNotFound("This OCDS dataset is not available for download")

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
