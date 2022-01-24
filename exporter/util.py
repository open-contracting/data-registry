import functools
import logging
import shutil
from pathlib import Path
from typing import List, Literal

from django.conf import settings
from yapw import clients

logger = logging.getLogger(__name__)


class Consumer(clients.Threaded, clients.Durable, clients.Blocking, clients.Base):
    pass


class Publisher(clients.Durable, clients.Blocking, clients.Base):
    pass


def get_client(klass):
    return klass(url=settings.RABBIT_URL, exchange=settings.RABBIT_EXCHANGE_NAME)


@functools.lru_cache(maxsize=None)
def get_consumer():
    return get_client(Consumer)


@functools.lru_cache(maxsize=None)
def get_publisher():
    return get_client(Publisher)


class Export:
    def __init__(self, *components):
        """
        :param components: the path components of the export directory
        """
        self.directory = Path(settings.EXPORTER_DIR).joinpath(*map(str, components))
        self.spoonbill_directory = Path(settings.SPOONBILL_EXPORTER_DIR).joinpath(*map(str, components))
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
