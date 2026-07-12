from django.apps import AppConfig


class SocialImpactV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.social_impact.v1"
    label = "social_impact_v1"
    verbose_name = "Social Impact (v1)"

    def ready(self):
        from . import signals  # noqa: F401
