from django.urls import path

from data_registry import i18n, views

urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("publication/<int:id>", views.detail, name="detail"),
    # https://code.djangoproject.com/ticket/26556
    path("i18n/setlang/", i18n.set_language, name="set-language"),
    # Uncomment after re-integrating Spoonbill.
    # path("excel-data/<int:job_id>/<str:job_range>", views.excel_data, name="excel-data"),
    # path("excel-data/<int:job_id>", views.excel_data, name="all-excel-data"),
]
