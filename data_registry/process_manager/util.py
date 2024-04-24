import logging
from abc import ABC, abstractmethod

import requests
from requests.exceptions import RequestException

from data_registry import models
from data_registry.exceptions import RecoverableException

logger = logging.getLogger(__name__)


class TaskManager(ABC):
    def __init__(self, task):
        """
        Initialize the task manager.

        This method must not assume that any previous tasks succeeded (for example, if it is called only to
        :meth:`~data_registry.process_manager.util.TaskManager.wipe`).
        """
        self.task = task

    @property
    def job(self) -> models.Job:
        """
        The job of which the task is a part.
        """
        return self.task.job

    @property
    def collection(self) -> models.Collection:
        """
        The publication on which the task is performed.
        """
        return self.task.job.collection

    @property
    @abstractmethod
    def final_output(self) -> bool:
        """
        Whether the task produces a final output, like a bulk download. If not, its intermediate outputs are wiped if
        the job is complete and isn't configured to preserve temporary data.
        """

    def request(self, method, url, *, error_message, **kwargs):
        """
        Send a request to the service. If the service returns an error response or is temporarily unavailable, raise
        :class:`~data_registry.exceptions.RecoverableException`.

        :raises RecoverableException:
        """
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            raise RecoverableException(f"{self}: {error_message} ({url})") from e

    @abstractmethod
    def run(self) -> None:
        """
        Start the task.

        This method is called once.

        :raises RecoverableException:
        """

    @abstractmethod
    def get_status(self) -> models.Task.Status:
        """
        Return the status of the task.

        This method can also write metadata about the task to the job. Since this method can be called multiple times,
        write metadata only when the metadata is missing or when the task is completed.

        This method must be called only after :meth:`~data_registry.process_manager.util.TaskManager.run` is called.

        :raises RecoverableException:
        """

    def wipe(self) -> None:
        """
        Delete any side effects of (for example, data written by) the task.

        This method must be idempotent. It is retried if any task failed to be wiped.

        Implement :meth:`~data_registry.process_manager.util.TaskManager.do_wipe` in subclasses.

        :raises RecoverableException:
        """
        if not self.task.start:
            logger.debug("%s has nothing to wipe (task didn't start)", self)
            return

        self.do_wipe()

    @abstractmethod
    def do_wipe(self) -> None:
        """
        Delete any side effects of the task.

        This method can assume that the task had started.

        :raises RecoverableException:
        """

    def __str__(self):
        return f"Publication {self.collection}: {self.__class__.__name__}"
