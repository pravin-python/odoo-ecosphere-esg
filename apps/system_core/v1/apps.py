from django.apps import AppConfig


class SystemCoreV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.system_core.v1"
    label = "system_core_v1"
    verbose_name = "System Core (v1)"
