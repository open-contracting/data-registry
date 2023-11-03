from django.urls import path

from exporter import views

urlpatterns = [
    path("publication/<int:id>/download", views.download_export, name="download"),
]
