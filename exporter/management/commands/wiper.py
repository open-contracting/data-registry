import json
import logging
import sys

from django.core.management.base import BaseCommand

from exporter.export.general import Export
from exporter.tools.rabbit import ack, consume

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Starts a worker to delete the files exported from collections in Kingfisher Process.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(callback, "_wiper_init")


def callback(connection, channel, delivery_tag, body):
    try:
        input_message = json.loads(body.decode("utf8"))
        logger.info("Processing message %s", input_message)

        export = Export(input_message.get("job_id"))
        export.remove()

        logger.info("Removed generated exports from %s", export.directory)
        ack(connection, channel, delivery_tag)
    except Exception:
        logger.exception("Something went wrong when processing %s", body)
        sys.exit()
