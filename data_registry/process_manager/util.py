import functools
import logging
from abc import ABC, abstractmethod

import requests
from requests.exceptions import RequestException

from data_registry import models
from data_registry.exceptions import RecoverableException
from exporter.util import TaskStatus

logger = logging.getLogger(__name__)


def exporter_status_to_task_status(status: TaskStatus) -> models.Task.Status:
    match status:
        case TaskStatus.WAITING:
            return models.Task.Status.WAITING
        case TaskStatus.RUNNING:
            return models.Task.Status.RUNNING
        case TaskStatus.COMPLETED:
            return models.Task.Status.COMPLETED


def skip_if_not_started(method):
    """
    A decorator to return early from a :meth:`~data_registry.process_manager.util.TaskManager.wipe` method if the task
    hadn't started.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.task.start:
            logger.debug("%s has nothing to wipe (task didn't start)", self)
            return

        method(self, *args, **kwargs)

    return wrapper


class TaskManager(ABC):
    """
    Task managers should only update the :class:`~data_registry.models.Job` context and metadata fields.
    """

    def __init__(self, task: models.Task):
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
        Whether the task produces a final output, like a bulk download.
        """

    def request(self, method, url, *, error_message, **kwargs):
        """
        Send a request to an application. If the application returns an error response or is temporarily unavailable,
        raise :class:`~data_registry.exceptions.RecoverableException`.

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

        This method must be called only after :meth:`~data_registry.process_manager.util.TaskManager.run` is called.

        This method can write metadata about the task to the job. Since this method can be called many times, write
        metadata only when the metadata is missing or when the task is complete.

        :raises RecoverableException:
        """

    @abstractmethod
    def wipe(self) -> None:
        """
        Delete any side effects of (for example, data written by) the task.

        This method can be called even when the task hasn't started.

        This method must be idempotent. It is retried if any task failed to be wiped.

        :raises RecoverableException:
        """

    def __str__(self):
        return f"Publication {self.collection}: {type(self).__name__}"
