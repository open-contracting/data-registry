from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from django.views import static

urlpatterns = [
    path('', include('data_registry.urls'), name='data_registry'),
    path('admin/', admin.site.urls),
    url(r'^markdownx/', include('markdownx.urls')),
]

if settings.DEBUG:
    urlpatterns = [
        url(r'^{}(?P<path>.*)$'.format(settings.STATIC_URL), static.serve, {'document_root': settings.STATIC_ROOT}),
    ] + urlpatterns
