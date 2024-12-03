from django.contrib import admin

ORDER = [
    "Collection",
    "License",
    "Job",
    "Task",
]


def _key(model):
    try:
        return str(ORDER.index(model["object_name"]))
    except ValueError:
        return model["name"]


class CoreAdminSite(admin.AdminSite):
    site_header = "Data registry administration"
    site_title = "Data registry administration"

    def get_app_list(self, request, app_label=None):
        """Sorts the data registry's models in a logical order."""
        app_list = super().get_app_list(request, app_label=app_label)

        if app := next((app for app in app_list if app["app_label"] == "data_registry"), None):
            app["models"].sort(key=_key)

        return app_list
