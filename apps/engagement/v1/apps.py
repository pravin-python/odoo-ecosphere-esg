from django.apps import AppConfig


class EngagementV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagement.v1"
    label = "engagement_v1"
    verbose_name = "Engagement (v1)"

    def ready(self):
        from . import signals  # noqa: F401
