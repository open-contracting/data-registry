from django.http import FileResponse
from django.http.response import HttpResponseNotFound

from exporter.util import Export


def download_export(request):
    """
    Returns an exported file as a FileResponse object.
    """
    spider = request.GET.get("spider")
    job_id = request.GET.get("job_id")
    full = request.GET.get("full")
    year = request.GET.get("year")

    export = Export(job_id)

    if full:
        dump_file = export.directory / "full.jsonl.gz"
        filename = f"{spider}_full.jsonl.gz"
    else:
        dump_file = export.directory / f"{year}.jsonl.gz"
        filename = f"{spider}_{year}.jsonl.gz"

    if export.running or not dump_file.exists():
        return HttpResponseNotFound("Unable to find export file")

    return FileResponse(dump_file.open("rb"), as_attachment=True, filename=filename)
