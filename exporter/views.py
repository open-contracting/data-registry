import json
import os
import re
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.http.response import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from exporter.tools.rabbit import publish


@csrf_exempt
def exporter_start(request):
    routing_key = "_exporter_init"

    input_message = json.loads(request.body.decode("utf8"))
    collection_id = input_message.get("collection_id")
    publish(request.body.decode("utf-8"), routing_key)

    return JsonResponse(
        {"status": "ok", "data": {"message": f"Export of collection {collection_id} started"}}, safe=False
    )


@csrf_exempt
def exporter_status(request):
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id")

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
    dump_file = f"{dump_dir}/full.jsonl.gz"
    lock_file = f"{dump_dir}/exporter.lock"

    status = "WAITING"
    if os.path.exists(lock_file):
        status = "RUNNING"
    elif os.path.exists(dump_file):
        status = "COMPLETED"

    return JsonResponse({"status": "ok", "data": status}, safe=False)


@csrf_exempt
def download_export(request):
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id")
    year = input_message.get("year", None)

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
    dump_file = f"{dump_dir}/{year}.jsonl.gz" if year else f"{dump_dir}/full.jsonl.gz"
    lock_file = f"{dump_dir}/exporter.lock"

    # reject download if the lock file exists (file is incomplete) or dump file doesn't exist
    if os.path.exists(lock_file) or not os.path.exists(dump_file):
        return HttpResponseNotFound("Unable to find export file")

    return FileResponse(
        open(dump_file, 'rb'),
        as_attachment=True,
        filename=f"{spider}_{year}" if year else f"{spider}_full",
        headers={
            'Content-Type': 'application/gzip'
        })


@csrf_exempt
def export_years(request):
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id")

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"

    # collect all years from annual dump files names
    years = [int(f.stem[:4]) for f in Path(dump_dir).glob("*") if f.is_file() and re.match("^[0-9]{4}", f.stem)]
    years.sort(reverse=True)
    return JsonResponse({"status": "ok", "data": years}, safe=False)
