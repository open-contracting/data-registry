import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.http.response import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt


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
    year = input_message.get("year", None)

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
    dump_file = f"{dump_dir}/{year}.jsonl.gz" if year else f"{dump_dir}/full.jsonl.gz"
    lock_file = f"{dump_dir}/exporter.lock"

    # reject download if the lock file exists (file is incomplete) or dump file doesn't exist
    if os.path.exists(lock_file) or not os.path.exists(dump_file):
        return HttpResponseNotFound("Unable to find export file")

    return FileResponse(
        open(dump_file, "rb"), as_attachment=True, filename=f"{spider}_{year}" if year else f"{spider}_full"
    )


@csrf_exempt
def export_years(request):
    """
    Returns the list of years for which there are exported files.

    Expects ``{"spider": <spider>, "job_id": <job_id>}`` in the request body.

    Returns ``{"status": "ok", "data": <sorted_list_of_years>}``.
    """
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id")

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"

    # collect all years from annual dump files names
    years = [int(f.stem[:4]) for f in Path(dump_dir).glob("*") if f.is_file() and re.match("^[0-9]{4}", f.stem)]
    # distinct values
    years = list(set(years))
    # descending sorting
    years.sort(reverse=True)
    return JsonResponse({"status": "ok", "data": years}, safe=False)
