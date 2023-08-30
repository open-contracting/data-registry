import logging

import requests
from requests.exceptions import RequestException

from data_registry.exceptions import RecoverableException
from data_registry.models import Task
from data_registry.process_manager.task.collect import Collect
from data_registry.process_manager.task.exporter import Exporter
from data_registry.process_manager.task.flattener import Flattener
from data_registry.process_manager.task.pelican import Pelican
from data_registry.process_manager.task.process import Process

logger = logging.getLogger(__name__)


def request(method, url, **kwargs):
    error_msg = kwargs.pop("error_msg", f"Request on {url} failed")
    consume_exception = kwargs.pop("consume_exception", False)

    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    except RequestException as e:
        if consume_exception:
            logger.exception(error_msg)
        else:
            raise RecoverableException(error_msg) from e


def get_runner(job, task):
    """
    Task classes must implement three methods:

    -  ``run()`` starts the task
    -  ``get_status()`` returns a choice from ``Task.Status``
    -  ``wipe()`` deletes any side-effects of ``run()``
    """

    match task.type:
        case Task.Type.COLLECT:
            return Collect(job.collection, job)
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
