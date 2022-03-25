import json

from django.http import FileResponse
from django.http.response import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from exporter.util import Export


@csrf_exempt
def download_export(request):
    """
    Returns an exported file as a FileResponse object.

    Expects ``{"spider": <spider>, "job_id": <job_id>, "year": 2021}`` in the request body.

    If ``year`` is omitted, the export file for the full collection is returned.
    """
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id").get("id")
    year = input_message.get("year")
    export_format = input_message.get("format")
    if export_format == "csv":
        export_format = f"{export_format}.tar"

    export = Export(job_id)
    if year:
        dump_file = export.directory / f"{year}.{export_format}.gz"
    else:
        dump_file = export.directory / f"full.{export_format}.gz"

    if export.running or not dump_file.exists():
        return HttpResponseNotFound("Unable to find export file")

    return FileResponse(
        dump_file.open("rb"),
        as_attachment=True,
        filename=f"{spider}_{year}_{export_format}" if year else f"{spider}_full_{export_format}",
    )
