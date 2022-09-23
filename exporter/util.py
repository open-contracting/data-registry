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
    @classmethod
    def get_files(cls, *components, **kwargs):
        components = [c for c in components if c]
        if components:
            return cls(*components, **kwargs).files
        return cls.default_files()

    @classmethod
    def default_files(cls):
        files = {}
        # Ensure the template always receives expected keys.
        for suffix in ("csv", "jsonl", "xlsx"):
            files[suffix] = {"years": set(), "full": False}
        return files

    def __init__(self, *components, export_type: str = "json"):
        """
        :param components: the path components of the export directory
        :param export_type: the export type, "json" or "flat" files (CSV and Excel)
        """
        self.directory = Path(settings.EXPORTER_DIR).joinpath(*map(str, components))
        self.spoonbill_directory = Path(settings.SPOONBILL_EXPORTER_DIR).joinpath(*map(str, components))
        self.lockfile = self.directory / f"exporter_{export_type}.lock"
        self.export_type = export_type

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
        if self.export_type == "json":
            filename = "full.jsonl.gz"
        else:
            filename = "full.csv.tar.gz"
        return (self.directory / filename).exists()

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

    @property
    def files(self) -> Dict:
        """
        Returns all the available file formats and segments (by year or full).
        """
        files = self.default_files()

        for path in self.directory.glob("*"):
            suffix = path.name.split(".", 2)[1]
            if suffix not in files:
                continue
            prefix = path.name[:4]  # year or "full"
            if prefix.isdigit() and "_" not in path.name:  # don't return month files
                files[suffix]["years"].add(int(prefix))
            elif prefix == "full":
                files[suffix]["full"] = True

        return files
