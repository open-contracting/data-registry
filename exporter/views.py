from django.http import FileResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from data_registry.models import Collection
from exporter.util import Export, TaskStatus


def download_export(request, id):
    """
    Returns an exported file as a FileResponse object.
    """
    name = request.GET.get("name")

    # Guard against path traversal.
    if not name.endswith(("jsonl.gz", "csv.tar.gz", "xlsx")):
        return HttpResponseBadRequest("Suffix not recognized")

    collection = get_object_or_404(Collection, id=id, public=True)

    active_job = collection.job.filter(active=True).first()
    if not active_job:
        return HttpResponseNotFound("No active job was found for this collection")

    export = Export(active_job.id, basename=f"{name}")

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
