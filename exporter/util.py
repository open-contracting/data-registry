import logging
import os
import shutil
from enum import StrEnum
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

from django.conf import settings
from django.db import connections
from yapw.clients import AsyncConsumer, Blocking
from yapw.decorators import decorate
from yapw.methods import add_callback_threadsafe, nack

from data_registry.exceptions import LockFileError

logger = logging.getLogger(__name__)


def get_client_kwargs(rabbit_params=None):
    if rabbit_params:
        parsed = urlsplit(settings.RABBIT_URL)
        query = parse_qs(parsed.query)
        query.update(rabbit_params)
        rabbit_url = parsed._replace(query=urlencode(query, doseq=True)).geturl()
    else:
        rabbit_url = settings.RABBIT_URL
    return {"url": rabbit_url, "exchange": settings.RABBIT_EXCHANGE_NAME}


def publish(*args, **kwargs):
    client = Blocking(**get_client_kwargs())
    try:
        client.publish(*args, **kwargs)
    finally:
        client.close()


def consume(*args, rabbit_params=None, **kwargs):
    client = AsyncConsumer(*args, **kwargs, **get_client_kwargs(rabbit_params))
    client.start()


def decorator(decode, callback, state, channel, method, properties, body):
    """
    Close the database connections opened by the callback, before returning.

    If the callback raises an exception, shut down the client in the main thread, without acknowledgment. For some
    exceptions, assume that the same message was delivered twice, log an error, and nack the message.
    """

    def errback(exception):
        if isinstance(exception, LockFileError):
            logger.exception("Locked since %s, maybe caused by duplicate message %r, skipping", exception, body)
            nack(state, channel, method.delivery_tag, requeue=False)
        else:
            logger.exception("Unhandled exception when consuming %r, shutting down gracefully", body)
            add_callback_threadsafe(state.connection, state.interrupt)

    def finalback():
        for conn in connections.all():
            conn.close()

    decorate(decode, callback, state, channel, method, properties, body, errback, finalback)


class TaskStatus(StrEnum):
    #: Processing hasn't started.
    WAITING = "WAITING"
    #: Processing has started.
    RUNNING = "RUNNING"
    #: Processing has ended.
    COMPLETED = "COMPLETED"


class Export:
    @classmethod
    def get_files(cls, *components, **kwargs):
        components = [c for c in components if c]
        if components:
            return cls(*components, **kwargs).files
        return cls.default_files()

    @classmethod
    def default_files(cls):
        return {
            "csv": {"full": False, "by_year": []},
            "jsonl": {"full": False, "by_year": []},
            "xlsx": {"full": False, "by_year": []},
        }

    def __init__(self, *components, basename: str | None = None):
        """
        ``basename`` is required to use ``lock()``, ``unlock()``, ``locked`` and ``status``.

        :param components: the path components of the export directory
        :param basename: the basename of the output file of the export operation
        """
        self.directory = Path(settings.EXPORTER_DIR).joinpath(*map(str, components))
        self.spoonbill_directory = Path(settings.SPOONBILL_EXPORTER_DIR).joinpath(*map(str, components))
        # Cause methods that require `basename` to error if the instance is improperly initialized.
        if basename:
            self.basename = basename

    def __str__(self):
        return f"{self.directory}/{self.basename}"

    def __repr__(self):
        return f"Export(directory={self.directory}, basename={self.basename})"

    @property
    def path(self):
        return self.directory / self.basename

    # This method's logic must match the workers' logic, so that views can get the status of an export task, by
    # providing only the desired filename.
    @property
    def lockfile(self) -> Path:
        # All JSONL files are exported at once.
        if self.basename.endswith(".jsonl.gz"):
            return self.directory / "exporter_full.jsonl.gz.lock"
        # Each XLSX file is exported with a CSV file.
        if self.basename.endswith(".xlsx"):
            return self.directory / f"exporter_{self.basename[:-5]}.csv.tar.gz.lock"
        return self.directory / f"exporter_{self.basename}.lock"

    def lock(self) -> None:
        """Create the lock file."""
        try:
            with self.lockfile.open("x"):
                pass
        except FileExistsError as e:
            raise LockFileError(self.lockfile.stat().st_mtime) from e

    def unlock(self) -> None:
        """Delete the lock file."""
        self.lockfile.unlink(missing_ok=True)

    def remove(self):
        """Delete the export directory recursively."""
        if self.directory.exists():
            shutil.rmtree(self.directory)

    @property
    def locked(self) -> bool:
        """Return whether the output file is being written."""
        return self.lockfile.exists()

    @property
    def status(self) -> TaskStatus:
        """Return the status of the export."""
        if self.locked:  # the output file is being written
            return TaskStatus.RUNNING
        if self.path.exists():  # the output file has been written
            return TaskStatus.COMPLETED
        return TaskStatus.WAITING

    @property
    def files(self) -> dict:
        """Return all the available file formats and segments (by year or full)."""
        files = self.default_files()

        for path in self.iterdir():
            suffix = path.name.split(".", 2)[1]  # works for .xlsx .jsonl.gz .csv.tar.gz
            if suffix not in files:
                continue
            prefix = path.name[:4]  # year or "full"
            if prefix.isdigit():
                files[suffix]["by_year"].append({"year": int(prefix), "size": os.path.getsize(path)})
            elif prefix == "full":
                files[suffix]["full"] = os.path.getsize(path)

        return files

    def iterdir(self):
        """Yield path objects of the directory contents."""
        if self.directory.exists():
            yield from self.directory.iterdir()

    def get_convertible_paths(self):
        """Yield paths to ``.jsonl.gz`` files."""
        for path in self.iterdir():
            if path.name.endswith(".jsonl.gz"):
                yield path
