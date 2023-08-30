from data_registry.models import Task
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
            case Task.Type.COLLECT:
                return Collect(collection, job)
            case Task.Type.PROCESS:
                return Process(job)
            case Task.Type.PELICAN:
                return Pelican(job)
            case Task.Type.EXPORTER:
                return Exporter(job)
            case Task.Type.FLATTENER:
                return Flattener(job)
            case _:
                raise Exception("Unsupported task type")
