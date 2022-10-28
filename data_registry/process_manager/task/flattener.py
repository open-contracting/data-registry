from data_registry.models import Task
from exporter.util import Export, TaskStatus, publish


class Flattener:
    def __init__(self, job):
        self.job = job

    def run(self):
        publish({"job_id": self.job.id}, "flattener_init")

    def get_status(self):
        status = Export(self.job.id, "full.csv.tar.gz").status
        if status == TaskStatus.WAITING:
            return Task.Status.WAITING
        if status == TaskStatus.RUNNING:
            return Task.Status.RUNNING
        if status == TaskStatus.COMPLETED:
            return Task.Status.COMPLETED

    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
