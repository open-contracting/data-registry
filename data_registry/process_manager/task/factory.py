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

        match task.type:
            case "collect":
                return Collect(collection, job)
            case "process":
                return Process(job)
            case "pelican":
                return Pelican(job)
            case "exporter":
                return Exporter(job)
            case "flattener":
                return Flattener(job)
            case _:
                raise Exception("Unsupported task type")
