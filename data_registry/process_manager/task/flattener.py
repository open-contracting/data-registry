from data_registry import models
from data_registry.process_manager.util import TaskManager, export_to_task_status, skip_if_not_started
from exporter.util import Export, TaskStatus, publish


class Flattener(TaskManager):
    final_output = True

    def get_exports(self):
        for path in Export(self.job.pk).get_convertible_paths():
            yield Export(self.job.pk, basename=f"{path.name[:-9]}.csv.tar.gz")  # remove .jsonl.gz

    def run(self):
        for export in self.get_exports():
            if export.locked:
                export.unlock()

        publish({"job_id": self.job.pk}, "flattener_init")

    def get_status(self):
        return next(
            (export_to_task_status(export) for export in self.get_exports() if export.status != TaskStatus.COMPLETED),
            models.Task.Status.COMPLETED,
        ), None

    @skip_if_not_started
    def wipe(self):
        # The exporter task already deletes the entire directory.
        pass
