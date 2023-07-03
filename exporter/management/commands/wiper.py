import logging

from django.core.management.base import BaseCommand
from yapw.methods import ack

from exporter.util import Export, consume

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Start a worker to delete the files exported from collections in Kingfisher Process.

    Multiple workers can run at the same time.
    """

    def handle(self, *args, **options):
        consume(on_message_callback=callback, queue="wiper_init")


def callback(state, channel, method, properties, input_message):
    export = Export(input_message.get("job_id"))
    export.remove()

    logger.info("Deleted %s", export.directory)
    ack(state, channel, method.delivery_tag)
