"""Gamification engine: award XP, auto-unlock badges, redeem rewards.

Kept out of signals/views so the rules live in one testable place.
"""
from django.db import transaction
from django.db.models import F

from apps.notifications.v1.models import Notification, notify

from .models import (
    Badge,
    BadgeUnlockRule,
    EmployeeProfile,
    Reward,
    RewardRedemption,
    UserBadge,
)

# Every 500 lifetime XP is one level.
XP_PER_LEVEL = 500


class RedemptionError(Exception):
    pass


def get_or_create_profile(user) -> EmployeeProfile:
    profile, _ = EmployeeProfile.objects.get_or_create(user=user)
    return profile


@transaction.atomic
def award_xp(user, amount: int, *, reason: str = "") -> EmployeeProfile:
    """Add XP to a user, recompute level, and auto-award any newly-earned badges."""
    profile = EmployeeProfile.objects.select_for_update().get_or_create(user=user)[0]
    profile.xp_balance = F("xp_balance") + amount
    profile.total_earned_xp = F("total_earned_xp") + amount
    profile.save(update_fields=["xp_balance", "total_earned_xp", "updated_at"])
    profile.refresh_from_db()

    new_level = max(1, profile.total_earned_xp // XP_PER_LEVEL + 1)
    if new_level != profile.level:
        profile.level = new_level
        profile.save(update_fields=["level", "updated_at"])

    notify(
        user,
        title=f"You earned {amount} XP",
        message=reason,
        category=Notification.Category.GAMIFICATION,
    )
    _evaluate_badges(profile)
    return profile


def _evaluate_badges(profile: EmployeeProfile):
    """Award every badge whose XP threshold the user now meets and hasn't got yet."""
    earned_badge_ids = set(
        UserBadge.objects.filter(profile=profile).values_list("badge_id", flat=True)
    )
    rules = BadgeUnlockRule.objects.filter(
        min_total_xp__lte=profile.total_earned_xp
    ).exclude(badge_id__in=earned_badge_ids).select_related("badge")

    for rule in rules:
        UserBadge.objects.get_or_create(profile=profile, badge=rule.badge)
        notify(
            profile.user,
            title=f"Badge unlocked: {rule.badge.name}",
            message=f"You reached {rule.min_total_xp} XP.",
            category=Notification.Category.GAMIFICATION,
        )


@transaction.atomic
def redeem_reward(user, reward: Reward) -> RewardRedemption:
    """Spend XP on a reward, decrementing stock atomically. Raises on failure."""
    profile = EmployeeProfile.objects.select_for_update().get(user=user)
    reward = Reward.objects.select_for_update().get(pk=reward.pk)

    if not reward.is_active or reward.stock_count < 1:
        raise RedemptionError("Reward is out of stock.")
    if profile.xp_balance < reward.points_required:
        raise RedemptionError("Insufficient XP balance.")

    profile.xp_balance = F("xp_balance") - reward.points_required
    profile.save(update_fields=["xp_balance", "updated_at"])
    reward.stock_count = F("stock_count") - 1
    reward.save(update_fields=["stock_count", "updated_at"])

    redemption = RewardRedemption.objects.create(
        profile=profile, reward=reward, points_spent=reward.points_required
    )
    notify(
        user,
        title=f"Reward claimed: {reward.name}",
        message=f"{reward.points_required} XP deducted.",
        category=Notification.Category.GAMIFICATION,
    )
    return redemption
