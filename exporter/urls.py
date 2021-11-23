from django.urls import path

from exporter.views import download_export

urlpatterns = [
    path("api/download_export", download_export, name="download_export"),
]
