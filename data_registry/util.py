import functools
from urllib.parse import urljoin

from django.conf import settings
from django.utils.formats import number_format

from data_registry.models import Collection


def scrapyd_url(path: str) -> str:
    """
    :param path: a `Scrapyd endpoint <https://scrapyd.readthedocs.io/en/latest/api.html>`__, like ``"schedule.json"``
    :return: an absolute URL to Scrapyd
    """
    return urljoin(settings.SCRAPYD["url"], path)


def collection_queryset(request):
    """
    If the user is not authenticated, limit to :meth:`~data_registry.models.CollectionQuerySet.visible` collections.
    """
    queryset = Collection.objects
    if not request.user.is_authenticated:
        return queryset.visible()
    return queryset


# https://stackoverflow.com/a/38911383
def partialclass(cls, *args, **kwargs):
    class NewCls(cls):
        __init__ = functools.partialmethod(cls.__init__, *args, **kwargs)

    return NewCls


def intcomma(value):
    return number_format(value, use_l10n=True, force_grouping=True)
