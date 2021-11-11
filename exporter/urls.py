from django.urls import path

from exporter.views import download_export, export_years, exporter_start, exporter_status, wiper_start

urlpatterns = [
    path("api/exporter_start", exporter_start, name="exporter_start"),
    path("api/wiper_start", wiper_start, name="wiper_start"),
    path("api/exporter_status", exporter_status, name="exporter_status"),
    path("api/download_export", download_export, name="download_export"),
    path("api/export_years", export_years, name="export_years"),
]
