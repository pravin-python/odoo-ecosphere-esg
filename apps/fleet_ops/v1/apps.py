from django.apps import AppConfig


class FleetOpsV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.fleet_ops.v1"
    label = "fleet_ops_v1"
    verbose_name = "Fleet Operations (v1)"

    def ready(self):
        from . import signals  # noqa: F401
