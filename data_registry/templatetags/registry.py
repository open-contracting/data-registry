import functools
from inspect import getfullargspec, unwrap
from urllib.parse import quote, urlencode

from django import template
from django.template.library import InclusionNode, parse_bits
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from data_registry.util import markdownify as render

register = template.Library()


class BlockInclusionNode(InclusionNode):
    def __init__(self, func, takes_context, args, kwargs, filename, nodelist):
        super().__init__(func, takes_context, args, kwargs, filename)
        self.nodelist = nodelist

    def render(self, context):
        context["content"] = self.nodelist.render(context)
        return super().render(context)


# https://docs.djangoproject.com/en/3.2/howto/custom-template-tags/#parsing-until-another-block-tag-and-saving-contents
# https://github.com/django/django/blob/stable/3.2.x/django/template/library.py#L136
# https://github.com/jameelhamdan/django-block-inclusion-tag/blob/master/tags.py
def block_inclusion_tag(filename, func=None, takes_context=None, name=None):
    def dec(func):
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(unwrap(func))
        function_name = name or getattr(func, "_decorated_function", func).__name__

        @functools.wraps(func)
        def compile_func(parser, token):
            bits = token.split_contents()[1:]
            args, kwargs = parse_bits(
                parser,
                bits,
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                takes_context,
                function_name,
            )

            nodelist = parser.parse((f"end{function_name}",))
            parser.delete_first_token()

            return BlockInclusionNode(
                func,
                takes_context,
                args,
                kwargs,
                filename,
                nodelist,
            )

        register.tag(function_name, compile_func)
        return func

    return dec


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


@register.inclusion_tag("includes/icon_chevron.html")
def icon_chevron(direction, classes=""):
    return {"direction": direction, "classes": classes}


@register.inclusion_tag("includes/icon_check.html")
def icon_check(checked, size="1em"):
    return {"checked": checked, "size": size}


@register.inclusion_tag("includes/facet_checkboxes.html", takes_context=True)
def checkboxes(context, title, key, items, facet_counts):
    return {
        "title": title,
        "key": key,
        "items": items,
        "facet_counts": facet_counts,
        "request": context["request"],
    }


@block_inclusion_tag("includes/facet_radiobuttons.html", takes_context=True)
def radiobuttons(context, title, key, items, facet_counts):
    return {
        "title": title,
        "key": key,
        "items": items,
        "facet_counts": facet_counts,
        "request": context["request"],
        "content": context["content"],  # passing the content via the context is simpler than via an arg
    }


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
