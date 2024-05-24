import json
import os.path
from urllib.parse import quote, urlencode

from django import template, urls
from django.apps import apps
from django.utils.safestring import mark_safe
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from django.utils.translation.trans_real import DjangoTranslation
from django.views.i18n import JavaScriptCatalog

from data_registry.util import markdownify as render

register = template.Library()


class CaptureNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        context[self.varname] = self.nodelist.render(context)
        return ""


@register.tag(name="capture")
def do_capture(parser, token):
    _, varname = token.split_contents()
    nodelist = parser.parse(("endcapture",))
    parser.delete_first_token()
    return CaptureNode(nodelist, varname)


@register.simple_tag()
def catalog_str():
    catalog = JavaScriptCatalog()
    catalog.translation = DjangoTranslation(
        get_language(),
        domain="djangojs",
        localedirs=[
            os.path.join(apps.get_app_config("data_registry").path, "locale"),
        ],
    )
    return mark_safe(json.dumps(catalog.get_catalog()))


@register.simple_tag(takes_context=True)
def canonical_url(context, language=None):
    request = context["request"]
    name = urls.resolve(request.path).url_name

    if language is None:
        language = get_language()

    match (name, language):
        case ("index", "en"):
            # / is the canonical of /en/.
            args = ["/"]
        case ("search", _):
            # Avoid duplicate content across different filters. Okay since there's no pagination.
            args = [urls.reverse("search")]
        case _:
            args = []
    return request.build_absolute_uri(*args)


@register.simple_tag(takes_context=True)
def translate_url(context, language):
    request = context["request"]
    name = urls.resolve(request.path).url_name

    url = canonical_url(context, language)
    if name == "index" and language == "en":
        # Translating "/es/" to "en" would return "/en/", which is not canonical.
        return url
    return urls.translate_url(url, language)


@register.simple_tag(takes_context=True)
def redirect_to(context):
    """
    Remove the ``letter`` query string parameter, to avoid zero results in the new language.
    """
    request = context["request"]
    if "letter" in request.GET:
        return request.build_absolute_uri(f"{request.path}?{remove_query_string_parameter(context, 'letter')}")
    return ""


@register.simple_tag(takes_context=True)
def replace_query_string_parameter(context, param, value):
    copy = context["request"].GET.copy()
    copy[param] = value
    return copy.urlencode()


@register.simple_tag(takes_context=True)
def remove_query_string_parameter(context, param):
    copy = context["request"].GET.copy()
    del copy[param]
    return copy.urlencode()


@register.simple_tag(takes_context=True)
def feedback_query_string_parameters(context):
    subject = _("[data-registry] Re: %(collection)s") % {"collection": context["collection"]}
    return urlencode({"subject": subject}, quote_via=quote)


@register.filter
def markdownify(value):
    return mark_safe(render(value))


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def getlist(query_dict, key):
    return query_dict.getlist(key, [""])  # Use "" as a default value for radio buttons, etc.


@register.filter
def sortreversed(sequence):
    return sorted(sequence, reverse=True)


@register.filter
def humanfilesize(size):
    size = max(0.1, size / 1000000)
    return f"{size:,.0f} MB" if size >= 1 else "< 1 MB"
