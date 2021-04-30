import logging

from data_registry.models import Job

logger = logging.getLogger('cbom')


def process(collection):
    logger.debug("Processing collection {}".format(collection))
    jobs = collection.jobs


def should_be_planned(collection):
    jobs = Job.objects.filter(collection = collection)
    if not jobs:
        return True
    else:
        return False
