from django.contrib import admin

from .models import (
    Badge,
    BadgeUnlockRule,
    Challenge,
    ChallengeParticipation,
    EmployeeProfile,
    Reward,
    RewardRedemption,
    UserBadge,
)


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "xp_balance", "total_earned_xp", "level")
    search_fields = ("user__username",)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "difficulty", "xp_reward", "status",
                    "deadline", "is_active")
    list_filter = ("status", "difficulty", "is_active")
    search_fields = ("title",)


@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ("employee", "challenge", "progress", "status", "xp_awarded",
                    "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("employee__username", "challenge__title")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "tier")
    list_filter = ("tier",)


@admin.register(BadgeUnlockRule)
class BadgeUnlockRuleAdmin(admin.ModelAdmin):
    list_display = ("badge", "min_total_xp")


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ("name", "points_required", "stock_count", "is_active")
    list_filter = ("is_active",)


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ("profile", "reward", "points_spent", "status", "created_at")
    list_filter = ("status",)


admin.site.register(UserBadge)
