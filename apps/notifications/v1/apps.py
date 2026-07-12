from django.apps import AppConfig


class NotificationsV1Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications.v1"
    label = "notifications_v1"
    verbose_name = "Notifications (v1)"
