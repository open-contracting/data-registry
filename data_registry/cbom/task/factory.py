
from data_registry.cbom.task.exporter import Exporter
from data_registry.cbom.task.pelican import Pelican
from data_registry.cbom.task.process import Process
from data_registry.cbom.task.scrape import Scrape


class TaskFactory:
    @staticmethod
    def get_task(collection, job, task):
        type = task.type

        if type == "scrape":
            return Scrape(collection, job)
        elif type == "process":
            return Process(job)
        elif type == "pelican":
            return Pelican(job)
        elif type == "exporter":
            return Exporter(job)
        else:
            raise Exception("Unsupported task type")
