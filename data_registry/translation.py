from modeltranslation.translator import TranslationOptions, register

from data_registry.models import Collection, Issue, License


@register(Collection)
class CollectionTranslation(TranslationOptions):
    fields = ['title', 'description', 'description_long', 'summary', 'additional_data', 'country']


@register(Issue)
class IssueTranslation(TranslationOptions):
    fields = ['description']


@register(License)
class LicenseTranslation(TranslationOptions):
    fields = ['name', 'description']
