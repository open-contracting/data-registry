import functools
from urllib.parse import urljoin

from django.conf import settings
from markdown_it import MarkdownIt

from data_registry.models import Collection


def scrapyd_url(path):
    return urljoin(settings.SCRAPYD["url"], path)


def collection_queryset(request):
    queryset = Collection.objects
    if not request.user.is_authenticated:
        return queryset.visible()
    return queryset


# https://markdown-it-py.readthedocs.io/en/latest/using.html#renderers
def render_blank_link(self, tokens, idx, options, env):
    tokens[idx].attrSet("target", "_blank")
    return self.renderToken(tokens, idx, options, env)


def markdownify(content):
    md = MarkdownIt("commonmark", {"typographer": True})
    md.enable(["smartquotes"])
    md.add_render_rule("link_open", render_blank_link)
    return md.render(content)


# https://stackoverflow.com/a/38911383
def partialclass(cls, *args, **kwargs):

    class NewCls(cls):
        __init__ = functools.partialmethod(cls.__init__, *args, **kwargs)

    return NewCls
