from django.urls import path

from exporter import views

urlpatterns = [
    path("api/download_export", views.download_export, name="download_export"),
]
