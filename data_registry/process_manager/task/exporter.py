import logging

from data_registry.models import Task
from data_registry.process_manager.task.task import BaseTask
from exporter.export.general import Export, exporter_start, wiper_start

logger = logging.getLogger(__name__)


class Exporter(BaseTask):
    job = None
    collection_id = None

    def __init__(self, job):
        self.job = job
        self.collection_id = self.job.context.get("process_id_pelican", None)

    def run(self):
        exporter_start(self.collection_id, self.job.context.get("spider"), self.job.id)

    def get_status(self):
        status = Export(self.job.id).status

        if status == "WAITING":
            return Task.Status.WAITING
        if status == "RUNNING":
            return Task.Status.RUNNING
        if status == "COMPLETED":
            return Task.Status.COMPLETED

    def wipe(self):
        wiper_start(self.job.context.get("spider"), self.job.id)
