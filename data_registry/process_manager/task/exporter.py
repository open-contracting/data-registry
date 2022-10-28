from data_registry.models import Task
from exporter.util import Export, TaskStatus, publish


class Exporter:
    def __init__(self, job):
        self.job = job
        self.collection_id = self.job.context.get("process_id_pelican")

    def run(self):
        publish({"collection_id": self.collection_id, "job_id": self.job.id}, "exporter_init")

    def get_status(self):
        status = Export(self.job.id, "full.jsonl.gz").status
        if status == TaskStatus.WAITING:
            return Task.Status.WAITING
        if status == TaskStatus.RUNNING:
            return Task.Status.RUNNING
        if status == TaskStatus.COMPLETED:
            return Task.Status.COMPLETED

    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
