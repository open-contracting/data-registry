import logging
import shutil
from pathlib import Path
from typing import Dict, Literal

import pika.exceptions
from django.conf import settings
from yapw import clients

logger = logging.getLogger(__name__)


class Consumer(clients.Threaded, clients.Durable, clients.Blocking, clients.Base):
    pass


class Publisher(clients.Durable, clients.Blocking, clients.Base):
    pass


def get_client(klass):
    return klass(url=settings.RABBIT_URL, exchange=settings.RABBIT_EXCHANGE_NAME)


# https://github.com/pika/pika/blob/master/examples/blocking_consume_recover_multiple_hosts.py
def consume(*args, **kwargs):
    while True:
        try:
            client = get_client(Consumer)
            client.consume(*args, **kwargs)
            break
        # Do not recover if the connection was closed by the broker.
        except pika.exceptions.ConnectionClosedByBroker as e:  # subclass of AMQPConnectionError
            logger.warning(e)
            break
        # Recover from "Connection reset by peer".
        except pika.exceptions.StreamLostError as e:  # subclass of AMQPConnectionError
            logger.warning(e)
            continue


def publish(*args, **kwargs):
    client = get_client(Publisher)
    try:
        client.publish(*args, **kwargs)
    finally:
        client.close()


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

    def formats_available(self) -> Dict:
        """
        Returns all the available file formats and segmentation (by years or full content).
        """
        formats = {}
        for file_name in self.directory.glob("*.gz"):
            file_format = file_name.name.split(".")[1]
            if file_format not in formats:
                formats[file_format] = {"years": [], "full": False}
            # year or full
            prefix = file_name.name[:4]
            if prefix.isdigit():
                if prefix not in formats[file_format]["years"]:
                    formats[file_format]["years"].append(prefix)
            else:
                formats[file_format]["full"] = True
        return formats
