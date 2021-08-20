from django.contrib.admin.apps import AdminConfig


class CoreAdminConfig(AdminConfig):
    default_site = 'core.admin.CoreAdminSite'
