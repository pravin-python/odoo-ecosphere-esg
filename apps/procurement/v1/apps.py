from django.apps import AppConfig


class ProcurementV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.procurement.v1"
    label = "procurement_v1"
    verbose_name = "Procurement (v1)"

    def ready(self):
        from . import signals  # noqa: F401
