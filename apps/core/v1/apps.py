from django.apps import AppConfig


class CoreV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core.v1"
    label = "core_v1"
    verbose_name = "Core (v1)"
