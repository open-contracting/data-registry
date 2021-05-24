from django.urls import path

from exporter.views import exporter_start, exporter_status

urlpatterns = [
    path('api/exporter_start', exporter_start, name='exporter_start'),
    path('api/exporter_status', exporter_status, name='exporter_status')
]
