from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag('fathom_snippet.html')
def fathom_analytics():
    key = None
    if hasattr(settings, 'FATHOM_KEY'):
        key = settings.FATHOM_KEY
        domain = settings.FATHOM_FATHOM_ANALYTICS_DOMAIN
    return {'fathom_key': key, 'fathom_analytics_domain': domain}
