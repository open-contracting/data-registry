from modeltranslation.translator import TranslationOptions, register

from data_registry.models import Collection, Issue, License

# django-modeltranslation always sets null=True:
# https://django-modeltranslation.readthedocs.io/en/latest/registration.html#required-langs
#
# To avoid having multiple values meaning "no value", we set `fallback_undefined = ""`:
# https://django-modeltranslation.readthedocs.io/en/latest/usage.html#fallback-undef


@register(Collection)
class CollectionTranslation(TranslationOptions):
    fields = ['title', 'description', 'description_long', 'summary', 'additional_data', 'country', 'language']
    fallback_undefined = ""


@register(Issue)
class IssueTranslation(TranslationOptions):
    fields = ['description']
    fallback_undefined = ""


@register(License)
class LicenseTranslation(TranslationOptions):
    fields = ['name', 'description']
    fallback_undefined = ""
