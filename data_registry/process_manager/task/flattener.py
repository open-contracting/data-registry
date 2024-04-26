from data_registry.process_manager.util import TaskManager, exporter_status_to_task_status, skip_if_not_started
from exporter.util import Export, publish


class Flattener(TaskManager):
    final_output = True

    def run(self):
        publish({"job_id": self.job.id}, "flattener_init")

    def get_status(self):
        status = Export(self.job.id, basename="full.csv.tar.gz").status
        return exporter_status_to_task_status(status)

    @skip_if_not_started
    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
