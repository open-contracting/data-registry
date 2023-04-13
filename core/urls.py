from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("data_registry.urls"), name="data-registry"),
    path("", include("exporter.urls"), name="exporter"),
    path("admin/", admin.site.urls),
    path("markdownx/", include("markdownx.urls")),
]

urlpatterns += i18n_patterns(path("", include("data_registry.urls"), name="data-registry"))
