from django.conf import settings
from modeltranslation.translator import TranslationOptions, register

from data_registry import models

# django-modeltranslation always sets null=True:
# https://django-modeltranslation.readthedocs.io/en/latest/registration.html#required-langs
#
# To avoid having multiple values meaning "no value", we set `fallback_undefined = ""`:
# https://django-modeltranslation.readthedocs.io/en/latest/usage.html#fallback-undef


@register(models.Collection)
class CollectionTranslation(TranslationOptions):
    fields = ["title", "description", "description_long", "summary", "additional_data", "country", "language"]
    required_languages = {language: ("title",) for language, _ in settings.LANGUAGES}
    fallback_undefined = ""


@register(models.License)
class LicenseTranslation(TranslationOptions):
    fields = ["name", "description"]
    fallback_undefined = ""
