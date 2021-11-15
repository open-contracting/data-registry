import logging

import requests
from requests.exceptions import RequestException

from data_registry.process_manager.task.exceptions import RecoverableException

logger = logging.getLogger(__name__)


def request(method, url, **kwargs):
    error_msg = kwargs.pop("error_msg", f"Request on {url} failed")
    consume_exception = kwargs.pop("consume_exception", False)

    try:
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp
    except RequestException as e:
        if consume_exception:
            logger.exception(error_msg)
        else:
            raise RecoverableException(error_msg) from e
