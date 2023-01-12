from django.http import FileResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound

from exporter.util import Export, TaskStatus


def download_export(request):
    """
    Returns an exported file as a FileResponse object.
    """
    job_id = int(request.GET.get("job_id") or 0)  # guard against path traversal
    full = request.GET.get("full")
    year = int(request.GET.get("year") or 0)  # guard against path traversal
    suffix = request.GET.get("suffix")
    spider = request.GET.get("spider")

    # Guard against path traversal.
    if suffix not in ("jsonl.gz", "csv.tar.gz", "xlsx"):
        return HttpResponseBadRequest("Suffix not recognized")

    stem = "full" if full else year
    export = Export(job_id, basename=f"{stem}.{suffix}")

    if export.status != TaskStatus.COMPLETED:
        return HttpResponseNotFound("File not found")

    return FileResponse(
        export.path.open("rb"),
        as_attachment=True,
        filename=f"{spider}_{stem}.{suffix}",
        # Set Content-Encoding to skip GZipMiddleware. (ContentEncodingMiddleware removes the empty header.)
        # https://docs.djangoproject.com/en/3.2/ref/middleware/#module-django.middleware.gzip
        headers={"Content-Encoding": ""},
    )
