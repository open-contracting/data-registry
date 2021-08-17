from django.urls import path

from data_registry.views import general

urlpatterns = [
    path('', general.index, name='index'),
    path('search/', general.search, name='search'),
    path('collection/<int:id>', general.detail, name='detail'),
    path('send_feedback/', general.send_feedback, name='send-feedback'),
    path('wipe_job/<int:job_id>', general.wipe_job, name='wipe-job'),
    path('excel_data/<int:job_id>/<str:job_range>', general.excel_data, name='excel_data')
]
