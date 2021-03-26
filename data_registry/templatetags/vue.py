from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def template_script(name):
    return mark_safe("""<script type="text/x-template" id="{}">""".format(name))


@register.simple_tag
def template_script_end():
    return mark_safe("</script>")


# @register.inclusion_tag('vue_templates/tender_list.html')
# def tender_list_vue_template():
#     return {}


# @register.inclusion_tag('vue_templates/research_form.html')
# def tender_research_form_template(search_criteria):
#     return {
#         'search_criteria': search_criteria,
#         'export_url': "/rest/tender_generate_pdf"
#     }

