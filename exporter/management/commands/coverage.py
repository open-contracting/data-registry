import gzip
import shutil
import tempfile
from pathlib import Path

from django.core.management import BaseCommand
from ocdscardinal import ocdscardinal
from yapw.methods import ack

from data_registry.models import Job
from exporter.util import Export, consume, decorator


class Command(BaseCommand):
    help = """Calculate the field coverage of JSON files."""

    def handle(self, *args, **options):
        consume(on_message_callback=callback, queue="coverage_init", decorator=decorator)


def filter_json_paths_by_suffix(json_paths, suffix):
    return tuple(json_path for json_path in json_paths if json_path.endswith(suffix))


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")

    with tempfile.TemporaryDirectory() as tmpdirname:
        infile = Path(tmpdirname) / "coverage.jsonl"

        with gzip.open(Export(job_id, basename="full.jsonl.gz").path) as i, infile.open("wb") as o:
            shutil.copyfileobj(i, o)

        coverage = ocdscardinal.coverage(str(infile))

    field_mapping = {
        "tenders_count": ("/tender/",),
        "tenderers_count": ("/tender/tenderers[]/",),
        "tenders_items_count": ("/tender/items[]/",),
        "parties_count": ("/parties[]/",),
        "awards_count": ("/awards[]/",),
        "awards_items_count": ("/awards[]/items[]/",),
        "awards_suppliers_count": ("/awards[]/suppliers[]/",),
        "contracts_count": ("/contracts[]/",),
        "contracts_items_count": ("/contracts[]/items[]/",),
        "contracts_transactions_count": ("/contracts[]/implementation/transactions[]/",),
        "documents_count": filter_json_paths_by_suffix(coverage, "/documents[]/"),
        "plannings_count": ("/planning/",),
        "milestones_count": filter_json_paths_by_suffix(coverage, "/milestones[]/"),
        "amendments_count": filter_json_paths_by_suffix(coverage, "/amendments[]/"),
    }

    job = Job.objects.get(pk=job_id)
    job.coverage = coverage
    for field_name, json_paths in field_mapping.items():
        setattr(job, field_name, sum(coverage.get(json_path, 0) for json_path in json_paths))
    job.save(update_fields=["modified", "coverage", *field_mapping])

    # "The default timeout value for RabbitMQ is 30 minutes." Cardinal processes at about 350 MB/s,
    # so the timeout is only a concern if datasets exceed 500 GB or the server is extremely busy.
    # https://www.rabbitmq.com/docs/consumers#acknowledgement-timeout
    ack(state, channel, method.delivery_tag)
