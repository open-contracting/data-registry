import gzip
import logging
import shutil
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections
from yapw.methods import ack

from exporter.util import Export, consume, decorator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Export JSON files from compiled collections in Kingfisher Process.

    Data is exported as gzipped line-delimited JSON files, with one file per year and one ``full.jsonl.gz`` file.
    """

    def handle(self, *args, **options):
        consume(on_message_callback=callback, queue="exporter_init", decorator=decorator)


def callback(state, channel, method, properties, input_message):
    collection_id = input_message.get("collection_id")
    job_id = input_message.get("job_id")

    export = Export(job_id, basename="full.json.gz")
    dump_file = export.directory / "full.jsonl"

    try:
        export.directory.mkdir(parents=True)
    except FileExistsError:
        # Empty the directory, because files are opened with mode="a".
        for path in export.iterdir():
            if path.is_file():
                path.unlink()

    export.lock()

    minimum_data_id = 0
    page = 1
    files = {}

    # Acknowledge now to avoid connection losses. The rest can run for hours and is irreversible anyhow.
    ack(state, channel, method.delivery_tag)

    while True:
        with connections["kingfisher_process"].cursor() as cursor:
            logger.debug("Processing page %s with data.id > %s", page, minimum_data_id)
            cursor.execute(
                """
                    SELECT
                        data.id,
                        data,
                        data ->> 'date'
                    FROM
                        compiled_release
                        JOIN data ON data.id = data_id
                    WHERE
                        collection_id = %s
                        AND data.id > %s
                    ORDER BY
                        data.id
                    LIMIT %s
                """,
                [collection_id, minimum_data_id, settings.EXPORTER_PAGE_SIZE],
            )

            records = cursor.fetchall()

        if not records:
            break

        with open(dump_file, "a") as full:
            files[dump_file] = full

            for data_id, data, date in records:
                minimum_data_id = data_id

                full.write(data)
                full.write("\n")

                if date is None:
                    logger.exception("No compiled release date")
                    continue

                try:
                    datetime.strptime(date[:7], "%Y-%m")
                except ValueError:
                    logger.exception("Bad compiled release date: '%s'", date)
                    continue

                year_path = export.directory / f"{int(date[:4])}.jsonl"
                if year_path not in files:
                    files[year_path] = year_path.open("a")

                files[year_path].write(data)
                files[year_path].write("\n")

                month_path = export.directory / f"{int(date[:4])}_{date[5:7]}.jsonl"
                if month_path not in files:
                    files[month_path] = month_path.open("a")

                files[month_path].write(data)
                files[month_path].write("\n")

        page = page + 1

        # Last page.
        if len(records) < settings.EXPORTER_PAGE_SIZE:
            break

    for path, file in files.items():
        file.close()

        with path.open("rb") as i, gzip.open(f"{path}.gz", "wb") as o:
            shutil.copyfileobj(i, o)

        path.unlink()

    export.unlock()
    logger.debug("Done %r", input_message)
