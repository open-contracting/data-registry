#!/usr/bin/env python
import contextlib
import json
import logging
import os
import sys
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import connections

from exporter.tools.rabbit import consume

logger = logging.getLogger('exporter')


def start():
    routing_key = "_exporter_init"

    consume(callback, routing_key)

    return


def callback(channel, method, properties, body):
    try:
        # parse input message
        input_message = json.loads(body.decode("utf8"))
        collection_id = input_message.get("collection_id")
        spider = input_message.get("spider")
        job_id = input_message.get("job_id")

        dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
        dump_file = f"{dump_dir}/compiled_releases"
        lock_file = f"{dump_file}.lock"

        with contextlib.suppress(FileNotFoundError):
            os.remove(dump_file)
        with contextlib.suppress(FileNotFoundError):
            os.remove(lock_file)

        Path(dump_dir).mkdir(parents=True, exist_ok=True)

        # create file lock
        with open(lock_file, 'x'):
            pass

        logger.info(f"Processing message {body}")

        page = 0
        rec_number = 0

        # load data from kf-process and save
        while True:
            with connections["kf_process"].cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT d.data
                        FROM compiled_release c
                        JOIN data d ON (c.data_id = d.id)
                        WHERE collection_id = %s
                        LIMIT {settings.EXPORTER_PAGE_SIZE} OFFSET {page * settings.EXPORTER_PAGE_SIZE}
                    """,
                    [collection_id]
                )

                records = cursor.fetchall()

            if not records:
                break

            with open(dump_file, 'a') as f:
                output = File(f)
                for i, r in enumerate(records):
                    rec_number += 1
                    if i > 0:
                        output.write("\n")

                    output.write(r[0])

            # last page
            if len(records) < settings.EXPORTER_PAGE_SIZE:
                break

            page += 1

        # remove lock file
        os.remove(lock_file)

        # acknowledge message processing
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.exception(f"Something went wrong when processing {body}")
        sys.exit()

    logger.info("Processing completed.")


if __name__ == "__main__":
    start()
