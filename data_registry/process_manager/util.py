import functools
import logging
from abc import ABC, abstractmethod

import requests
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.urls import reverse

from data_registry import models
from data_registry.exceptions import RecoverableError
from data_registry.util import CHANGE
from exporter.util import Export, TaskStatus

logger = logging.getLogger(__name__)


def export_to_task_status(export: Export) -> models.Task.Status:
    match export.status:
        case TaskStatus.WAITING:
            return models.Task.Status.WAITING
        case TaskStatus.RUNNING:
            return models.Task.Status.RUNNING
        case TaskStatus.COMPLETED:
            return models.Task.Status.COMPLETED


def skip_if_not_started(method):
    """
    Decorate a :meth:`~data_registry.process_manager.util.TaskManager.wipe` method to return early if the task
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
    """Task managers should only update the :class:`~data_registry.models.Job` context and metadata fields."""

    def __init__(self, task: models.Task):
        """
        Initialize the task manager.

        This method must not assume that any previous tasks succeeded (for example, if it is called only to
        :meth:`~data_registry.process_manager.util.TaskManager.wipe`).
        """
        self.task = task

    @property
    def job(self) -> models.Job:
        """The job of which the task is a part."""
        return self.task.job

    @property
    def collection(self) -> models.Collection:
        """The publication on which the task is performed."""
        return self.task.job.collection

    @property
    def job_url(self) -> str:
        """The URL to the job's admin change page."""
        path = reverse(CHANGE.format(content_type=ContentType.objects.get_for_model(models.Job)), args=[self.job.pk])
        return f"https://{Site.objects.get_current().domain}{path}"

    @property
    @abstractmethod
    def final_output(self) -> bool:
        """
        Whether the task produces a final output, like a bulk download.

        If False, then once a job is complete, the "manageprocess" management command calls
        :meth:`~data_registry.process_manager.util.TaskManager.wipe` (unless temporary data is to be preserved).
        """

    def request(self, method, url, *, error_message, timeout=10, **kwargs):
        """
        Send a request to an application.

        If the application returns an error response or is temporarily unavailable,
        raise :class:`~data_registry.exceptions.RecoverableError`.

        :raises RecoverableError:
        """
        try:
            response = requests.request(method, url, **kwargs, timeout=timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RecoverableError(f"{self}: {error_message} ({url})") from e
        return response

    @abstractmethod
    def run(self) -> None:
        """
        Start the task.

        This method is called once.

        :raises RecoverableError: if the task can't be started, temporarily
        """

    @abstractmethod
    def get_status(self) -> models.Task.Status:
        """
        Return the status of the task.

        This method must be called only after :meth:`~data_registry.process_manager.util.TaskManager.run` is called.

        This method can write metadata about the task to the job. Since this method can be called many times, write
        metadata only when the metadata is missing or when the task is complete.

        This method is expected to be called within a transaction.

        :raises RecoverableError:
        """

    @abstractmethod
    def wipe(self) -> None:
        """
        Delete any side effects of (for example, data written by) the task.

        This method can be called even when the task hasn't started.

        This method must be idempotent. It is retried if any task failed to be wiped.

        :raises RecoverableError:
        """

    def __str__(self):
        return f"Publication {self.collection}: Job #{self.job.pk}: {type(self).__name__}"
