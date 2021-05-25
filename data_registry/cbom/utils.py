import requests
from requests.exceptions import RequestException

from data_registry.cbom.task.exceptions import RecoverableException


def request(method, url, **kwargs):
    error_msg = kwargs.pop("error_msg", f"Request on {url} failed")

    try:
        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp
    except RequestException as e:
        raise RecoverableException(error_msg) from e
