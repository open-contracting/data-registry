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
    help = """
    Get the coverage of exported full JSONL compiled collections using Cardinal.
    """

    def handle(self, *args, **options):
        consume(on_message_callback=callback, queue="coverage_init", decorator=decorator)


def filter_json_paths_by_suffix(json_paths, suffix):
    return [json_path for json_path in json_paths if json_path.endswith(suffix)]


def callback(state, channel, method, properties, input_message):
    job_id = input_message.get("job_id")
    job = Job.objects.get(id=job_id)

    export = Export(job_id, basename="coverage")

    export.lock()

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    with tempfile.TemporaryDirectory() as tmpdirname:
        infile = Path(tmpdirname) / "coverage.jsonl"

        with gzip.open(Export(job_id, "full.jsonl.gz").path) as i, infile.open("wb") as o:
            shutil.copyfileobj(i, o)

        coverage = ocdscardinal.coverage(str(infile))

        attributes_mapping = {
            "tenders_count": ("/tender/",),
            "tenderers_count": ("/tender/tenderers[]",),
            "tenders_items_count": ("/tender/items[]",),
            "parties_count": ("/parties[]",),
            "awards_count": ("/awards[]",),
            "awards_items_count": ("/awards[]/items[]",),
            "awards_suppliers_count": ("/awards[]/suppliers[]",),
            "contracts_count": ("/contracts[]",),
            "contracts_items_count": ("/contracts[]/items[]",),
            "contracts_transactions_count": ("/contracts[]/transactions[]",),
            "documents_count": filter_json_paths_by_suffix(coverage, "documents[]"),
            "plannings_count": ("/planning/",),
            "milestones_count": filter_json_paths_by_suffix(coverage, "milestones[]"),
            "amendments_count": filter_json_paths_by_suffix(coverage, "amendments[]"),
        }
        for attribute, json_paths in attributes_mapping.items():
            setattr(job, attribute, sum(coverage.get(json_path, 0) for json_path in json_paths))

        job.coverage = coverage
        job.save(update_fields=["modified", "coverage", *attributes_mapping])

    export.unlock()
