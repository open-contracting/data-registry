import gzip
import shutil
import tempfile
from pathlib import Path

import ocdscardinal

from data_registry import models
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from exporter.util import Export


def filter_json_paths_by_suffix(json_paths, suffix):
    return [json_path for json_path in json_paths if json_path.endswith(suffix)]


class Coverage(TaskManager):
    final_output = True

    def get_export(self):
        return Export(self.job.pk, basename="coverage")

    def run(self):
        export = self.get_export()

        export.lock()

        with tempfile.TemporaryDirectory() as tmpdirname:
            infile = Path(tmpdirname) / "coverage.jsonl"

            with gzip.open(Export(self.job.pk, "full.jsonl.gz").path) as i, infile.open("wb") as o:
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
                setattr(self.job, attribute, sum(coverage.get(json_path, 0) for json_path in json_paths))

            self.job.context["coverage"] = coverage
            self.job.save(update_fields=["modified", "coverage", *attributes_mapping])

        export.unlock()

    def get_status(self):
        if self.get_export().locked:
            return models.Task.Status.RUNNING
        if "coverage" in self.job.context:
            return models.Task.Status.COMPLETED
        return models.Task.Status.WAITING

    @skip_if_not_started
    def wipe(self):
        # The exporter task already deletes the entire directory.
        pass
