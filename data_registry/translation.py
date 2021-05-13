from modeltranslation.translator import TranslationOptions, register

from data_registry.models import Collection, Issue


@register(Collection)
class CollectionTranslation(TranslationOptions):
    fields = ['title', 'description', 'description_long']


@register(Issue)
class IssueTranslation(TranslationOptions):
    fields = ['description']
