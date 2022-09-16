from django.urls import path

from data_registry import views

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("publication/<int:id>", views.detail, name="detail"),
    path("wipe_job/<int:job_id>", views.wipe_job, name="wipe-job"),
    # Uncomment after re-integrating Spoonbill.
    # path("excel_data/<int:job_id>/<str:job_range>", views.excel_data, name="excel_data"),
    # path("excel_data/<int:job_id>", views.excel_data, name="all_excel_data"),
]
