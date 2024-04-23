from data_registry.models import Task
from data_registry.process_manager.util import TaskManager
from exporter.util import Export, TaskStatus, publish


class Flattener(TaskManager):
    def run(self):
        publish({"job_id": self.job.id}, "flattener_init")

    def get_status(self):
        match Export(self.job.id, basename="full.csv.tar.gz").status:
            case TaskStatus.WAITING:
                return Task.Status.WAITING
            case TaskStatus.RUNNING:
                return Task.Status.RUNNING
            case TaskStatus.COMPLETED:
                return Task.Status.COMPLETED

    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
