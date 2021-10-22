#!/usr/bin/env python
import json
import logging
import os
import shutil
import sys

from django.conf import settings

from exporter.tools.rabbit import ack, consume

logger = logging.getLogger(__name__)


def start():
    routing_key = "_wiper_init"

    consume(callback, routing_key)

    return


def callback(connection, channel, delivery_tag, body):
    try:
        # parse input message
        input_message = json.loads(body.decode("utf8"))
        spider = input_message.get("spider")
        job_id = input_message.get("job_id")

        dump_dir = "{}/{}/{}".format(settings.EXPORTER_DIR, spider, job_id)

        logger.info("Processing message {}".format(input_message))

        if os.path.exists(dump_dir):
            shutil.rmtree(dump_dir)

        logger.info("Removed generated exports from {}".format(dump_dir))

        # acknowledge message processing
        ack(connection, channel, delivery_tag)
    except Exception:
        logger.exception(f"Something went wrong when processing {body}")
        sys.exit()

    logger.info("Processing completed.")


if __name__ == "__main__":
    start()
