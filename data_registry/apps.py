from django.apps import AppConfig


class DataRegistryConfig(AppConfig):
    name = "data_registry"
    verbose_name = "Data registry"

    def ready(self):
        from data_registry import signals  # noqa: F401
