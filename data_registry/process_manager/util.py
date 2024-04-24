import logging
from abc import ABC, abstractmethod

import requests
from requests.exceptions import RequestException

from data_registry.exceptions import RecoverableException
from data_registry.models import Task

logger = logging.getLogger(__name__)


class TaskManager(ABC):
    def __init__(self, job):
        self.job = job

    def request(self, method, url, **kwargs):
        error_msg = kwargs.pop("error_msg", "Request failed")
        error_msg = f"{self}: {error_msg} ({url})"
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

    @abstractmethod
    def run(self) -> None:
        """
        Start the task.
        """
        pass

    @abstractmethod
    def get_status(self) -> Task.Status:
        """
        Return the status of the task.

        This method can also write metadata about the task to the job. Since this method can be called multiple times,
        write metadata only when the metadata is missing or when the task is completed.
        """
        pass

    @abstractmethod
    def wipe(self) -> None:
        """
        Delete any side effects of (for example, data written by) the task.
        """
        pass

    def __str__(self):
        return f"Publication {self.job.collection}: {self.__class__.__name__}"
