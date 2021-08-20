from django.conf import settings
from django.conf.urls import url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from django.views import static

urlpatterns = [
    path('', include('data_registry.urls'), name='data_registry'),
    path('', include('exporter.urls'), name='exporter'),
    path('admin/', admin.site.urls),
    url(r'^markdownx/', include('markdownx.urls')),
    path('i18n/', include('django.conf.urls.i18n'))
]


urlpatterns += i18n_patterns(
    path('', include('data_registry.urls'), name='data_registry')
)

if settings.DEBUG:
    urlpatterns = [
        url(
            r'^{}(?P<path>.*)$'.format(settings.STATIC_URL[1:]),
            static.serve,
            {'document_root': settings.STATIC_ROOT}
        ),
    ] + urlpatterns
