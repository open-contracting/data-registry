from django.apps import AppConfig


class DataRegistryConfig(AppConfig):
    name = "data_registry"
    verbose_name = "Data registry"

    def ready(self):
        # https://docs.djangoproject.com/en/5.2/topics/signals/
        from data_registry import signals  # noqa: F401, PLC0415
