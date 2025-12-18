import logging

from django.core.management.base import BaseCommand

from data_registry.models import Collection
from data_registry.process_manager import delete_older_jobs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete old jobs"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done, without making changes")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            logger.info("DRY RUN: No actions are actually performed")

        for collection in Collection.objects.all():
            if collection.active_job:
                delete_older_jobs(collection, collection.active_job, dry_run=dry_run)
            else:
                logger.warning("No active job for collection %s: %s", collection.country, collection)
