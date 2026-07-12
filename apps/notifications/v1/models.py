from django.conf import settings
from django.db import models

from apps.core.v1.models import TimeStampedModel


class Notification(TimeStampedModel):
    """In-app alert. Created by signals for approvals, badges, and overdue issues."""

    class Category(models.TextChoices):
        COMPLIANCE = "COMPLIANCE", "Compliance"
        CSR = "CSR", "CSR"
        GAMIFICATION = "GAMIFICATION", "Gamification"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.SYSTEM)
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["recipient", "is_read"])]

    def __str__(self):
        return f"[{self.category}] {self.title} -> {self.recipient}"


def notify(recipient, title, *, message="", category=Notification.Category.SYSTEM):
    """Convenience helper used by signals across the platform.

    Notifications are system-generated for a specific recipient, so the insert
    runs under rls_admin(): the acting user (e.g. a manager creating a
    compliance issue) is usually not the recipient, and the owner-scoped RLS
    policy on Notification would otherwise reject the row.
    """
    if recipient is None:
        return None
    from apps.core.v1.rls.context import rls_admin

    with rls_admin():
        return Notification.objects.create(
            recipient=recipient, title=title, message=message, category=category
        )
