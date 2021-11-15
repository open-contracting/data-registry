from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def template_script(name):
    return mark_safe(f'<script type="text/x-template" id="{name}">')


@register.simple_tag
def template_script_end():
    return mark_safe("</script>")


@register.inclusion_tag("vue/chevron_btn.html")
def chevron_btn_vue_template():
    return {}


@register.inclusion_tag("vue/check_icon.html")
def check_icon_vue_template():
    return {}


@register.inclusion_tag("vue/dropdown.html")
def dropdown_vue_template():
    return {}


@register.inclusion_tag("vue/modal.html")
def modal_vue_template():
    return {}


@register.inclusion_tag("vue/markdown_box.html")
def markdown_box_vue_template():
    return {}
