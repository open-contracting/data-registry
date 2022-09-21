import logging

from data_registry.models import Task
from exporter.util import Export, publish

logger = logging.getLogger(__name__)


class Flattener:
    def __init__(self, job):
        self.job = job

    def run(self):
        publish({"job_id": self.job.id}, "flattener_init")

    def get_status(self):
        status = Export(self.job.id, export_type="flat").status
        if status == "WAITING":
            return Task.Status.WAITING
        if status == "RUNNING":
            return Task.Status.RUNNING
        if status == "COMPLETED":
            return Task.Status.COMPLETED

    def wipe(self):
        publish({"job_id": self.job.id}, "wiper_init")
