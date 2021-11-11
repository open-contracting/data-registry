from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views import static

urlpatterns = [
    path("", include("data_registry.urls"), name="data_registry"),
    path("", include("exporter.urls"), name="exporter"),
    path("admin/", admin.site.urls),
    path("markdownx/", include("markdownx.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
]


urlpatterns += i18n_patterns(path("", include("data_registry.urls"), name="data_registry"))

if settings.DEBUG:
    # https://docs.djangoproject.com/en/3.2/ref/contrib/staticfiles/#static-file-development-view
    # https://docs.djangoproject.com/en/3.2/ref/views/#django.views.static.serve
    urlpatterns += [re_path(r"^static/(?P<path>.*)$", static.serve, {"document_root": settings.STATIC_ROOT})]
