import logging
import shutil
from pathlib import Path
from typing import List, Literal

from django.conf import settings

from exporter.tools.rabbit import publish

logger = logging.getLogger(__name__)


class Export:
    def __init__(self, *components):
        """
        :param components: the path components of the export directory
        """
        self.directory = Path(settings.EXPORTER_DIR).joinpath(*components)
        self.lockfile = self.directory / "exporter.lock"

    def lock(self) -> None:
        """
        Create the lock file.
        """
        with self.lockfile.open("x"):
            pass

    def unlock(self) -> None:
        """
        Delete the lock file.
        """
        self.lockfile.unlink()

    def remove(self):
        """
        Delete the export directory recursively.
        """
        if self.directory.exists():
            shutil.rmtree(self.directory)

    @property
    def running(self) -> bool:
        """
        Return whether the exported file is being written.
        """
        return self.lockfile.exists()

    @property
    def completed(self) -> bool:
        """
        Return whether the final file has been written.
        """
        return (self.directory / "full.jsonl.gz").exists()

    @property
    def status(self) -> Literal["RUNNING", "COMPLETED", "WAITING"]:
        """
        Return the status of the export.
        """
        if self.running:
            return "RUNNING"
        if self.completed:
            return "COMPLETED"
        return "WAITING"

    def years_available(self) -> List[int]:
        """
        Return the calendar years for which there are exported files in reverse chronological order.
        """
        return sorted((int(p.name[:4]) for p in self.directory.glob("[0-9][0-9][0-9][0-9].jsonl.gz")), reverse=True)


def exporter_start(collection_id, spider, job_id):
    """
    Adds a message to a queue to export files from a collection in Kingfisher Process.

    :param int collection_id: id of the collection in Kingfisher Process
    :param str spider: spider name
    :param int job_id: id of the job to deleted
    """
    routing_key = "_exporter_init"

    message = {"collection_id": collection_id, "spider": spider, "job_id": job_id}

    publish(message, routing_key)
    logger.info(
        "Published message to start export of collection_id %s spider %s job_id %s", collection_id, spider, job_id
    )


def wiper_start(spider, job_id):
    """
    Adds a message to a queue to delete the files exported from a collection.

    :param str spider: spider name
    :param int job_id: id of the job to deleted
    """
    routing_key = "_wiper_init"

    message = {"spider": spider, "job_id": job_id}

    publish(message, routing_key)
    logger.info("Published message to wipe exported of spider %s job_id %s", spider, job_id)
