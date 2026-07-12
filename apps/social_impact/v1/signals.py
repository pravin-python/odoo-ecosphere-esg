from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.v1.enums import ApprovalStatus
from apps.engagement.v1.services import award_xp
from apps.notifications.v1.models import Notification, notify

from .models import EmployeeParticipation


@receiver(post_save, sender=EmployeeParticipation, dispatch_uid="csr_participation_xp")
def award_xp_on_approval(sender, instance, **kwargs):
    """When a manager approves a CSR participation, grant the activity's XP once
    and notify the employee of the approval decision."""
    if instance.status == ApprovalStatus.APPROVED and not instance.xp_awarded:
        award_xp(
            instance.employee,
            instance.activity.xp_reward,
            reason=f"CSR approved: {instance.activity.title}",
        )
        # Mark as awarded without re-triggering this handler.
        EmployeeParticipation.objects.filter(pk=instance.pk).update(xp_awarded=True)
    elif instance.status == ApprovalStatus.REJECTED:
        notify(
            instance.employee,
            title=f"CSR participation rejected: {instance.activity.title}",
            message=instance.review_notes or "Your submission was not approved.",
            category=Notification.Category.CSR,
        )
