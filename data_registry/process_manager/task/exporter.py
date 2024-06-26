from data_registry.process_manager.util import TaskManager, exporter_status_to_task_status, skip_if_not_started
from exporter.util import Export, publish


class Exporter(TaskManager):
    final_output = True

    def get_export(self):
        return Export(self.job.id, basename="full.jsonl.gz")

    def run(self):
        self.get_export().unlock()

        publish({"job_id": self.job.id, "collection_id": self.job.context["process_id_pelican"]}, "exporter_init")

    def get_status(self):
        export = self.get_export()

        return exporter_status_to_task_status(export.status)

    @skip_if_not_started
    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
