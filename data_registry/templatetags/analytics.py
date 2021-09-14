from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag('fathom_snippet.html')
def fathom_analytics():
    key = None
    domain = None
    if hasattr(settings, 'FATHOM_ANALYTICS_ID'):
        key = settings.FATHOM_ANALYTICS_ID
        domain = settings.FATHOM_ANALYTICS_DOMAIN
    return {'fathom_analytics_id': key, 'fathom_analytics_domain': domain}
