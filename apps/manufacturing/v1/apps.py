from django.apps import AppConfig


class ManufacturingV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.manufacturing.v1"
    label = "manufacturing_v1"
    verbose_name = "Manufacturing (v1)"

    def ready(self):
        from . import signals  # noqa: F401
