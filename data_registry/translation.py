from modeltranslation.translator import TranslationOptions, register

from data_registry.models import Collection


@register(Collection)
class CollectionTranslation(TranslationOptions):
    fields = ('title', 'description', 'description_long')
