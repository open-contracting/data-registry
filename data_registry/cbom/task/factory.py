
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
        else:
            raise Exception("Unsupported task type")
