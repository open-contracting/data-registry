
from data_registry.cbom.task.scrape import Scrape


class TaskFactory:
    @staticmethod
    def get_task(collection, job, task):
        type = task.type

        if type == "scrape":
            return Scrape(collection, task)
        else:
            raise Exception("Unsupported task type")
