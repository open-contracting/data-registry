import logging
import os
import re
from pathlib import Path

from django.conf import settings

from exporter.tools.rabbit import publish

logger = logging.getLogger(__name__)


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


def exporter_status(spider, job_id):
    """
    Returns the status of an exporter job task.

    :param str spider: name of the spider
    :param int job_id: id of the export job

    :returns: one of ("WAITING", "RUNNING", "COMPLETED")
    :rtype: str
    """

    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
    dump_file = f"{dump_dir}/full.jsonl.gz"
    lock_file = f"{dump_dir}/exporter.lock"

    status = "WAITING"
    if os.path.exists(lock_file):
        status = "RUNNING"
    elif os.path.exists(dump_file):
        status = "COMPLETED"

    return status


def export_years(spider, job_id):
    """
    Returns the list of years for which there are exported files.

    :param str spider: name of the spider
    :param int job_id: id of the export job

    :returns: sorted list of years
    :rtype: list
    """
    dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"

    # collect all years from annual dump files names
    years = list({int(f.stem[:4]) for f in Path(dump_dir).glob("*") if f.is_file() and re.match("^[0-9]{4}", f.stem)})
    years.sort(reverse=True)
    return years
