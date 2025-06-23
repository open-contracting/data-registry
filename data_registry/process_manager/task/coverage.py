import gzip
import shutil
import tempfile
from pathlib import Path

import ocdscardinal

from data_registry import models
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from exporter.util import Export


def get_keys_for_building_block(coverage, building_block):
    return [key for key in coverage if key.endswith(building_block)]


class Coverage(TaskManager):
    final_output = False
    json_file_name = "full.jsonl"

    def get_export(self):
        return Export(self.job.pk, f"{self.json_file_name}.gz")

    def run(self):
        export = self.get_export()
        export.lock()
        json_file_path = export.path
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)
            infile = tmpdir / self.json_file_name
            with gzip.open(json_file_path) as i, infile.open("wb") as o:
                shutil.copyfileobj(i, o)
                coverage = ocdscardinal.coverage(o.name)
                mapping = {
                    "tenders_count": "/tender/",
                    "tenderers_count": "/tender/tenderers[]",
                    "tenders_items_count": "/tender/items[]",
                    "parties_count": "/parties[]",
                    "awards_count": "/awards[]",
                    "awards_items_count": "/awards[]/items[]",
                    "awards_suppliers_count": "/awards[]/suppliers[]",
                    "contracts_count": "/contracts[]",
                    "contracts_items_count": "/contracts[]/items[]",
                    "contracts_transactions_count": "/contracts[]/transactions[]",
                    "documents_count": get_keys_for_building_block(coverage, "documents[]"),
                    "plannings_count": "/planning/",
                    "milestones_count": get_keys_for_building_block(coverage, "milestones[]"),
                    "amendments_count": get_keys_for_building_block(coverage, "amendments[]"),
                }
                for key, value in mapping.items():
                    if type(value, list):
                        setattr(self.job, key, 0)
                        for subkey in value:
                            setattr(self.job, key, getattr(self.job, key) + coverage.get(subkey))
                    else:
                        setattr(self.job, key, coverage.get(value, 0))
                self.job.context["full_coverage"] = coverage
                self.job.save(update_fields=["modified", *mapping])
        export.unlock()

    def get_status(self):
        if self.get_export().locked:
            return models.Task.Status.RUNNING

        return models.Task.Status.COMPLETED

    @skip_if_not_started
    def wipe(self):
        # The coverage task already deletes the entire directory.
        pass
