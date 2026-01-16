from data_registry import models
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from exporter.util import publish


class Coverage(TaskManager):
    final_output = True

    def run(self):
        publish({"job_id": self.job.pk}, "coverage_init")

    def get_status(self):
        # It might be running, not waiting, but the effect is the same. The server would need to be busy, or the file
        # size would need to be >100 GB, for processing time to exceed the 5-minute window between manageprocess runs.
        return models.Task.Status.COMPLETED if self.job.coverage else models.Task.Status.WAITING, None

    @skip_if_not_started
    def wipe(self):
        # The exporter task already deletes the entire directory.
        pass
