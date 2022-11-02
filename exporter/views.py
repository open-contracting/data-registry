from django.http import FileResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound

from exporter.util import Export, TaskStatus


def download_export(request):
    """
    Returns an exported file as a FileResponse object.
    """
    spider = request.GET.get("spider")
    job_id = request.GET.get("job_id")
    full = request.GET.get("full")
    year = request.GET.get("year")
    suffix = request.GET.get("suffix")

    # Guard against path traversal.
    if suffix not in ("jsonl.gz", "csv.tar.gz", "xlsx"):
        return HttpResponseBadRequest("Suffix not recognized")

    # Set Content-Encoding to skip GZipMiddleware.
    # https://docs.djangoproject.com/en/3.2/ref/middleware/#module-django.middleware.gzip
    headers = {}
    if suffix in ("jsonl.gz", "csv.tar.gz"):
        headers = {"Content-Encoding": "gzip"}

    if full:
        basename = f"full.{suffix}"
        filename = f"{spider}_full.{suffix}"
    else:
        # Guard against path traversal.
        year = int(year)
        basename = f"{year}.{suffix}"
        filename = f"{spider}_{year}.{suffix}"

    export = Export(job_id, basename=basename)

    if export.status != TaskStatus.COMPLETED:
        return HttpResponseNotFound("File not found")

    return FileResponse(export.path.open("rb"), as_attachment=True, filename=filename, headers=headers)
