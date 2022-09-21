from django.http import FileResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound

from exporter.util import Export


def download_export(request):
    """
    Returns an exported file as a FileResponse object.
    """
    spider = request.GET.get("spider")
    job_id = request.GET.get("job_id")
    full = request.GET.get("full")
    year = int(request.GET.get("year"))  # guard against path traversal
    suffix = request.GET.get("format")

    # Guard against path traversal.
    if suffix not in ("jsonl.gz", "csv.tar.gz", "xlsx"):
        return HttpResponseBadRequest("Format not recognized")

    export = Export(job_id)

    if full:
        dump_file = export.directory / f"full.{suffix}"
        filename = f"{spider}_full.{suffix}"
    else:
        dump_file = export.directory / f"{year}.{suffix}"
        filename = f"{spider}_{year}.{suffix}"

    if export.running or not dump_file.exists():
        return HttpResponseNotFound("File not found")

    return FileResponse(dump_file.open("rb"), as_attachment=True, filename=filename)
