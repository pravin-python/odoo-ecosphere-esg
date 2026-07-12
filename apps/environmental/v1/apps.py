from django.apps import AppConfig


class EnvironmentalV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.environmental.v1"
    label = "environmental_v1"
    verbose_name = "Environmental (v1)"
