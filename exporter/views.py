from django.http import FileResponse
from django.http.response import HttpResponseNotFound

from exporter.management.commands import flattener
from exporter.util import Export


def download_export(request):
    """
    Returns an exported file as a FileResponse object.
    """
    spider = request.GET.get("spider")
    job_id = request.GET.get("job_id")
    full = request.GET.get("full")
    year = request.GET.get("year")
    export_format = request.GET.get("export_format")
    if export_format == "csv":
        export_format = f"{export_format}.tar"

    export = Export(job_id)

    if full:
        dump_file = export.directory / f"full.{export_format}.gz"
        filename = f"{spider}_full.{export_format}.gz"
    else:
        dump_file = export.directory / f"{year}.{export_format}.gz"
        filename = f"{spider}_{year}.{export_format}.gz"

    if export.running or not dump_file.exists():
        return HttpResponseNotFound("Unable to find export file")

    return FileResponse(dump_file.open("rb"), as_attachment=True, filename=filename)
