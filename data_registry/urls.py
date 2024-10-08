from django.contrib.sitemaps.views import sitemap
from django.urls import path

from data_registry import i18n, sitemaps, views

maps = {
    "static": sitemaps.StaticViewSitemap,
    "detail": sitemaps.CollectionSitemap,
}

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("publication/<int:pk>", views.detail, name="detail"),
    path("publication/<int:pk>/download", views.download_export, name="download"),
    path("publications.json", views.publications_api, name="publications_api"),
    # Uncomment after re-integrating Spoonbill.
    # path("excel-data/<int:job_id>/<str:job_range>", views.excel_data, name="excel-data"),  # noqa: ERA001
    # path("excel-data/<int:job_id>", views.excel_data, name="all-excel-data"),  # noqa: ERA001
    # https://code.djangoproject.com/ticket/26556
    path("i18n/setlang/", i18n.set_language, name="set-language"),
    path("sitemap.xml", sitemap, {"sitemaps": maps}, name="django.contrib.sitemaps.views.sitemap"),
]
