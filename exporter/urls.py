from django.urls import path

from exporter.views import download_export, export_years

urlpatterns = [
    path("api/download_export", download_export, name="download_export"),
    path("api/export_years", export_years, name="export_years"),
]
