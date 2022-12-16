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
    if suffix == "jsonl.gz":
        # https://stackoverflow.com/a/67807011/244258
        headers = {"Content-Encoding": "gzip", "Content-Type": "application/jsonlines+json"}
        extension = "jsonl"
    if suffix == "csv.tar.gz":
        # https://stackoverflow.com/a/57954148/244258
        headers = {"Content-Encoding": "gzip", "Content-Type": "application/x-tar"}
        extension = "csv.tar"
    else:
        headers = {}
        extension = suffix

    if full:
        stem = "full"
    else:
        stem = int(year)  # guard against path traversal

    export = Export(job_id, basename=f"{stem}.{extension}")

    if export.status != TaskStatus.COMPLETED:
        return HttpResponseNotFound("File not found")

    return FileResponse(
        export.path.open("rb"), as_attachment=True, filename=f"{spider}_{stem}.{extension}", headers=headers
    )
