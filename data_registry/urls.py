from django.urls import path

from data_registry.views import general

urlpatterns = [
    path('', general.index, name='index'),
]
