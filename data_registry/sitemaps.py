from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from data_registry import models


class StaticViewSitemap(Sitemap):
    i18n = True
    alternates = True
    protocol = "http" if settings.DEBUG else "https"

    def items(self):
        return ["index", "search"]

    def location(self, item):
        return reverse(item)


class CollectionSitemap(Sitemap):
    i18n = True
    alternates = True
    protocol = "http" if settings.DEBUG else "https"

    # See data_registry.util.collection_queryset().
    def items(self):
        return models.Collection.objects.visible()

    def location(self, item):
        return reverse("detail", kwargs={"pk": item.pk})

    def lastmod(self, obj):
        return obj.modified
