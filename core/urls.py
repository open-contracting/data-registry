import re

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("", include("data_registry.urls"), name="data-registry"),
    path("admin/", admin.site.urls),
]

urlpatterns += i18n_patterns(path("", include("data_registry.urls"), name="data-registry"))

if settings.SERVE_STATIC:
    # Emulate static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # https://github.com/django/django/blob/stable/5.2.x/django/conf/urls/static.py
    urlpatterns += [
        re_path(
            rf"^{re.escape(settings.STATIC_URL.lstrip('/'))}(?P<path>.*)$",
            serve,
            {"document_root": settings.STATIC_ROOT},
        ),
    ]
