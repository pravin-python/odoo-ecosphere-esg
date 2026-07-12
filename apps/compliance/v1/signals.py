from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.v1.models import Notification, notify

from .models import ComplianceIssue


@receiver(post_save, sender=ComplianceIssue, dispatch_uid="compliance_issue_raised")
def notify_owner_on_issue(sender, instance, created, **kwargs):
    """Alert the assigned owner the moment a compliance issue is raised."""
    if not created:
        return
    notify(
        instance.owner,
        title=f"New compliance issue: {instance.title}",
        message=(
            f"Severity {instance.get_severity_display()} — due {instance.due_date}. "
            f"You are the assigned owner."
        ),
        category=Notification.Category.COMPLIANCE,
    )
