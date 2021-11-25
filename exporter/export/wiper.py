#!/usr/bin/env python
import json
import logging
import sys

from exporter.export.general import Export
from exporter.tools.rabbit import ack, consume

logger = logging.getLogger(__name__)


def start():
    routing_key = "_wiper_init"

    consume(callback, routing_key)

    return


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

    logger.info("Processing completed.")


if __name__ == "__main__":
    start()
