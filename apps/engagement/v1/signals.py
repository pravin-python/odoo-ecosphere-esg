from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.v1.enums import ApprovalStatus
from apps.notifications.v1.models import Notification, notify

from .models import ChallengeParticipation
from .services import award_xp, get_or_create_profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid="create_employee_profile")
def create_profile_for_user(sender, instance, created, **kwargs):
    """Every new user gets a gamification profile automatically.

    Runs under rls_admin() because user creation happens in contexts with no
    RLS session (createsuperuser, the public register endpoint, data loaders),
    where the owner WITH CHECK on EmployeeProfile would otherwise reject the row.
    """
    if created:
        from apps.core.v1.rls.context import rls_admin

        with rls_admin():
            get_or_create_profile(instance)


@receiver(post_save, sender=ChallengeParticipation, dispatch_uid="challenge_participation_xp")
def award_xp_on_challenge_approval(sender, instance, **kwargs):
    """Grant the challenge's XP once, when a manager approves participation."""
    if instance.status == ApprovalStatus.APPROVED and not instance.xp_awarded:
        award_xp(
            instance.employee,
            instance.challenge.xp_reward,
            reason=f"Challenge approved: {instance.challenge.title}",
        )
        ChallengeParticipation.objects.filter(pk=instance.pk).update(xp_awarded=True)
    elif instance.status == ApprovalStatus.REJECTED:
        notify(
            instance.employee,
            title=f"Challenge submission rejected: {instance.challenge.title}",
            message="Your challenge submission was not approved.",
            category=Notification.Category.GAMIFICATION,
        )
