from django.apps import AppConfig


class ReportingV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reporting.v1"
    label = "reporting_v1"
    verbose_name = "Reporting (v1)"
