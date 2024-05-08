from data_registry import models
from data_registry.process_manager.util import TaskManager, exporter_status_to_task_status, skip_if_not_started
from exporter.util import Export, publish


class Flattener(TaskManager):
    final_output = True

    def get_exports(self):
        export = Export(self.job.id)
        for path in export.get_convertible_paths():
            yield Export(self.job.id, basename=f"{path.name[:-9]}.csv.tar.gz")  # remove .jsonl.gz

    def run(self):
        for export in self.get_exports():
            if export.running:
                export.unlock()

        publish({"job_id": self.job.id}, "flattener_init")

    def get_status(self):
        for export in self.get_exports():
            if not export.completed:
                return exporter_status_to_task_status(export.status)

        return models.Task.Status.COMPLETED

    @skip_if_not_started
    def wipe(self):
        # The exporter task already deletes the entire directory.
        pass
