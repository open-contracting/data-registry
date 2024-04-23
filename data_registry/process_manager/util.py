import logging

import requests
from requests.exceptions import RequestException

from data_registry.exceptions import RecoverableException

logger = logging.getLogger(__name__)


class TaskManager:
    def __init__(self, job):
        self.job = job

    def request(self, method, url, **kwargs):
        error_msg = kwargs.pop("error_msg", f"Request on {url} failed")
        error_msg = f"{self}: {error_msg}"
        consume_exception = kwargs.pop("consume_exception", False)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            if consume_exception:
                logger.exception(error_msg)
            else:
                raise RecoverableException(error_msg) from e

    def __str__(self):
        return f"Publication {self.job.collection}: {self.__class__.__name__}"
