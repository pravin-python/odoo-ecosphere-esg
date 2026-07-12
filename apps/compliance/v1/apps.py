from django.apps import AppConfig


class ComplianceV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.compliance.v1"
    label = "compliance_v1"
    verbose_name = "Compliance (v1)"

    def ready(self):
        from . import signals  # noqa: F401
