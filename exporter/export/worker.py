#!/usr/bin/env python
import json
import logging
import os
import sys
from pathlib import Path

from django.conf import settings
from django.db import connections

from exporter.tools.rabbit import consume

logger = logging.getLogger('exporter')

touched_files = None


def start():
    routing_key = "_exporter_init"

    consume(callback, routing_key)

    return


def callback(channel, method, properties, body):
    try:
        # reset list of touched files
        global touched_files
        touched_files = set()

        # parse input message
        input_message = json.loads(body.decode("utf8"))
        collection_id = input_message.get("collection_id")
        spider = input_message.get("spider")
        job_id = input_message.get("job_id")

        dump_dir = f"{settings.EXPORTER_DIR}/{spider}/{job_id}"
        dump_file = f"{dump_dir}/full"
        lock_file = f"{dump_dir}/exporter.lock"

        try:
            Path(dump_dir).mkdir(parents=True)
        except FileExistsError:
            [f.unlink() for f in Path(dump_dir).glob("*") if f.is_file()]

        # create file lock
        with open(lock_file, 'x'):
            pass

        logger.info(f"Processing message {body}")

        page = 0

        # load data from kf-process and save
        while True:
            with connections["kf_process"].cursor() as cursor:
                cursor.execute(
                    f"""
                        SELECT d.data, EXTRACT(YEAR from (d.data->>'date')::DATE)
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

            with open(dump_file, 'a') as full:
                for r in records:
                    # full dump
                    append_file_line(full, r[0])

                    # annual dump
                    with open(f"{dump_dir}/{int(r[1])}", 'a') as annual:
                        append_file_line(annual, r[0])

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


def append_file_line(file, line):
    global touched_files

    if file in touched_files:
        file.write("\n")

    touched_files.add(file.name)
    file.write(line)


if __name__ == "__main__":
    start()
