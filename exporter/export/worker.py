#!/usr/bin/env python
import gzip
import json
import logging
import shutil
import sys

from django.conf import settings
from django.db import connections

from exporter.export.general import Export
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
        job_id = input_message.get("job_id")

        export = Export(job_id)
        dump_file = export.directory / "full.jsonl"

        try:
            export.directory.mkdir(parents=True)
        except FileExistsError:
            [f.unlink() for f in export.directory.glob("*") if f.is_file()]

        export.lock()

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

                    full.write(r[1])
                    full.write("\n")

                    # annual and monthly dump
                    if r[2] is not None and len(r[2]) > 9:
                        year_path = export.directory / f"{int(r[2][:4])}.jsonl"
                        if year_path not in files:
                            files[year_path] = year_path.open("a")

                        files[year_path].write(r[1])
                        files[year_path].write("\n")

                        month_path = export.directory / f"{int(r[2][:4])}_{r[2][5:7]}.jsonl"
                        if month_path not in files:
                            files[month_path] = month_path.open("a")

                        files[month_path].write(r[1])
                        files[month_path].write("\n")
            page = page + 1

            # last page
            if len(records) < settings.EXPORTER_PAGE_SIZE:
                break

        for path, file in files.items():
            file.close()

            with path.open("rb") as f_in:
                with gzip.open(f"{path}.gz", "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            path.unlink()

        export.unlock()

    except Exception:
        logger.exception("Something went wrong when processing %s", body)
        sys.exit()

    logger.info("Processing completed.")


if __name__ == "__main__":
    start()
