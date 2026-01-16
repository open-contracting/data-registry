import logging

from data_registry.process_manager.util import TaskManager, export_to_task_status, skip_if_not_started
from exporter.util import Export, publish

logger = logging.getLogger(__name__)


class Exporter(TaskManager):
    final_output = True

    def get_export(self):
        return Export(self.job.pk, basename="full.jsonl.gz")

    def run(self):
        self.get_export().unlock()

        publish(
            {"job_id": self.job.pk, "collection_id": self.job.context["process_compiled_collection_id"]},
            "exporter_init",
        )

    def get_status(self):
        return export_to_task_status(self.get_export()), None

    @skip_if_not_started
    def wipe(self):
        logger.info("%s: Wiping exported data", self)
        publish({"job_id": self.job.pk}, "wiper_init")
