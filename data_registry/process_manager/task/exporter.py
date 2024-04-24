from data_registry.models import Task
from data_registry.process_manager.util import TaskManager
from exporter.util import Export, TaskStatus, publish


class Exporter(TaskManager):
    @property
    def final_output(self):
        return True

    def run(self):
        publish({"collection_id": self.job.context["process_id_pelican"], "job_id": self.job.id}, "exporter_init")

    def get_status(self):
        match Export(self.job.id, basename="full.jsonl.gz").status:
            case TaskStatus.WAITING:
                return Task.Status.WAITING
            case TaskStatus.RUNNING:
                return Task.Status.RUNNING
            case TaskStatus.COMPLETED:
                return Task.Status.COMPLETED

    def do_wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
