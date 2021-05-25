import json
import os

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from exporter.tools.rabbit import publish


@csrf_exempt
def exporter_start(request):
    routing_key = "_exporter_init"

    input_message = json.loads(request.body.decode("utf8"))
    collection_id = input_message.get("collection_id")
    publish(json.dumps(request.body.decode("utf-8")), routing_key)

    return JsonResponse(
        {"status": "ok", "data": {"message": f"Export of collection {collection_id} started"}}, safe=False
    )


@csrf_exempt
def exporter_status(request):
    input_message = json.loads(request.body.decode("utf8"))

    spider = input_message.get("spider")
    job_id = input_message.get("job_id")

    dump_file = f"{settings.EXPORTER_DIR}/{spider}/{job_id}/compiled_releases"
    lock_file = f"{dump_file}.lock"

    status = "WAITING"
    if os.path.exists(lock_file):
        status = "RUNNING"
    elif os.path.exists(dump_file):
        status = "COMPLETED"

    return JsonResponse({"status": "ok", "data": status}, safe=False)
