from data_registry.models import Task
from data_registry.process_manager.util import TaskManager, skip_if_not_started
from exporter.util import Export, TaskStatus, publish


class Exporter(TaskManager):
    @property
    def final_output(self):
        return True

    def run(self):
        publish({"job_id": self.job.id, "collection_id": self.job.context["process_id_pelican"]}, "exporter_init")

    def get_status(self):
        match Export(self.job.id, basename="full.jsonl.gz").status:
            case TaskStatus.WAITING:
                return Task.Status.WAITING
            case TaskStatus.RUNNING:
                return Task.Status.RUNNING
            case TaskStatus.COMPLETED:
                return Task.Status.COMPLETED

    @skip_if_not_started
    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
