from data_registry import models
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from exporter.util import Export, publish


def filter_json_paths_by_suffix(json_paths, suffix):
    return [json_path for json_path in json_paths if json_path.endswith(suffix)]


class Coverage(TaskManager):
    final_output = True

    def get_export(self):
        return Export(self.job.pk, basename="coverage")

    def run(self):
        self.get_export().unlock()
        publish({"job_id": self.job.pk}, "coverage_init")

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
