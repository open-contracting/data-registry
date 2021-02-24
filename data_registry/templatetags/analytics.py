from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag('fathom_snippet.html')
def fathom_analytics():
    key = None
    if hasattr(settings, 'FATHOM_KEY'):
        key = settings.FATHOM_KEY
    return {'fathom_key': key}
