#!/usr/bin/env python
import gzip
import json
import logging
import os
import shutil
import sys
from pathlib import Path

from django.conf import settings
from django.db import connections

from exporter.tools.rabbit import ack, consume

logger = logging.getLogger(__name__)


def start():
    routing_key = "_exporter_init"

    consume(callback, routing_key)

    return


def callback(connection, channel, delivery_tag, body):
    try:
        # parse input message
        input_message = json.loads(body.decode("utf8"))
        collection_id = input_message.get("collection_id")
        spider = input_message.get("spider")
        job_id = input_message.get("job_id")

        dump_dir = "{}/{}/{}".format(settings.EXPORTER_DIR, spider, job_id)
        dump_file = "{}/{}".format(dump_dir, "full.jsonl")
        lock_file = "{}/exporter.lock".format(dump_dir)

        try:
            Path(dump_dir).mkdir(parents=True)
        except FileExistsError:
            [f.unlink() for f in Path(dump_dir).glob("*") if f.is_file()]

        # create file lock
        with open(lock_file, "x"):
            pass

        logger.info("Processing message %s", input_message)

        id = 0
        page = 1
        files = {}

        # acknowledge message processing now to avoid connection loses
        # the rest can run for hours and is irreversible anyways
        ack(connection, channel, delivery_tag)

        # load data from kf-process and save
        while True:
            with connections["kingfisher_process"].cursor() as cursor:
                logger.debug("Processing page %s with id > %s", page, id)
                cursor.execute(
                    """
                        SELECT d.id, d.data, d.data->>'date'
                        FROM compiled_release c
                        JOIN data d ON (c.data_id = d.id)
                        WHERE collection_id = %s
                        AND d.id > %s
                        ORDER BY d.id
                        LIMIT %s
                    """,
                    [collection_id, id, settings.EXPORTER_PAGE_SIZE],
                )

                records = cursor.fetchall()

            if not records:
                break

            with open(dump_file, "a") as full:
                files[dump_file] = full

                for r in records:
                    id = r[0]

                    full.write("{}\n".format(r[1]))

                    # annual and monthly dump
                    if r[2] is not None and len(r[2]) > 9:
                        year_key = "{}/{}.jsonl".format(dump_dir, int(r[2][:4]))
                        if year_key not in files:
                            files[year_key] = open(year_key, "a")

                        files[year_key].write("{}\n".format(r[1]))

                        month_key = "{}/{}_{}.jsonl".format(dump_dir, int(r[2][:4]), r[2][5:7])
                        if month_key not in files:
                            files[month_key] = open(month_key, "a")

                        files[month_key].write("{}\n".format(r[1]))
            page = page + 1

            # last page
            if len(records) < settings.EXPORTER_PAGE_SIZE:
                break

        for key, file in files.items():
            file.close()

            with open(key, "rb") as f_in:
                with gzip.open("{}.gz".format(key), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(key)

        # remove lock file
        os.remove(lock_file)

    except Exception:
        logger.exception("Something went wrong when processing %s", body)
        sys.exit()

    logger.info("Processing completed.")


if __name__ == "__main__":
    start()
