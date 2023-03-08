from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process


class TaskFactory:
    @staticmethod
    def get_task(collection, job, task):
        """
        Task classes must implement three methods:

        -  ``run()`` starts the task
        -  ``get_status()`` returns a choice from ``Task.Status``
        -  ``wipe()`` deletes any side-effects of ``run()``
        """

        type = task.type

        if type == "collect":
            return Collect(collection, job)
        elif type == "process":
            return Process(job)
        elif type == "pelican":
            return Pelican(job)
        elif type == "exporter":
            return Exporter(job)
        elif type == "flattener":
            return Flattener(job)
        else:
            raise Exception("Unsupported task type")
