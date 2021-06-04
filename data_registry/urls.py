from django.urls import path

from data_registry.views import general

urlpatterns = [
    path('', general.index, name='index'),
    path('search/', general.search, name='search'),
    path('collection/<int:id>', general.detail, name='detail'),
    path('send_feedback/', general.send_feedback, name='send-feedback')
]
