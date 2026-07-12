from django.conf import settings
from django.db import models

from apps.core.v1.enums import ApprovalStatus
from apps.core.v1.models import BaseModel, TimeStampedModel


class EmployeeProfile(TimeStampedModel):
    """Gamification extension of the user — holds the running XP balance."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    xp_balance = models.PositiveIntegerField(default=0, help_text="Spendable XP.")
    total_earned_xp = models.PositiveIntegerField(default=0, help_text="Lifetime XP earned.")
    level = models.PositiveSmallIntegerField(default=1)
    badges = models.ManyToManyField("Badge", through="UserBadge", related_name="holders", blank=True)

    class Meta:
        ordering = ("-total_earned_xp",)

    def __str__(self):
        return f"{self.user} — {self.xp_balance} XP"


class Challenge(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ACTIVE = "ACTIVE", "Active"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        COMPLETED = "COMPLETED", "Completed"
        ARCHIVED = "ARCHIVED", "Archived"

    class Difficulty(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        "system_core_v1.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"type": "CHALLENGE"},
        related_name="challenges",
    )
    xp_reward = models.PositiveIntegerField(default=0)
    difficulty = models.CharField(
        max_length=8, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    evidence_required = models.BooleanField(
        default=True, help_text="Require proof upload before participation can be approved."
    )
    start_date = models.DateField()
    end_date = models.DateField()
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-start_date",)

    def __str__(self):
        return self.title


class Badge(BaseModel):
    class Tier(models.TextChoices):
        BRONZE = "BRONZE", "Bronze"
        SILVER = "SILVER", "Silver"
        GOLD = "GOLD", "Gold"

    name = models.CharField(max_length=120, unique=True)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=64, blank=True, help_text="Icon name/emoji for the UI.")
    tier = models.CharField(max_length=10, choices=Tier.choices, default=Tier.BRONZE)

    class Meta:
        ordering = ("tier", "name")

    def __str__(self):
        return self.name


class BadgeUnlockRule(BaseModel):
    """Threshold criteria evaluated whenever a user's XP changes."""

    badge = models.OneToOneField(Badge, on_delete=models.CASCADE, related_name="unlock_rule")
    min_total_xp = models.PositiveIntegerField(help_text="Award when lifetime XP reaches this.")

    class Meta:
        ordering = ("min_total_xp",)

    def __str__(self):
        return f"{self.badge.name} @ {self.min_total_xp} XP"


class UserBadge(TimeStampedModel):
    profile = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "badge"], name="uniq_profile_badge")
        ]

    def __str__(self):
        return f"{self.profile.user} earned {self.badge.name}"


class Reward(BaseModel):
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    points_required = models.PositiveIntegerField()
    stock_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("points_required",)

    def __str__(self):
        return f"{self.name} ({self.points_required} XP)"


class RewardRedemption(BaseModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    profile = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name="redemptions"
    )
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name="redemptions")
    points_spent = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.profile.user} -> {self.reward.name}"


def challenge_evidence_path(instance, filename):
    return f"challenge_evidence/{instance.challenge_id}/{filename}"


class ChallengeParticipation(BaseModel):
    """Tracks an employee's progress within a Challenge (separate from CSR
    participation). XP is awarded once, on manager approval."""

    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="participations"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_participations"
    )
    progress = models.PositiveSmallIntegerField(default=0, help_text="Completion percent 0-100.")
    proof_file = models.FileField(upload_to=challenge_evidence_path, blank=True)
    status = models.CharField(
        max_length=12, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_challenge_participations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    xp_awarded = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "employee"], name="uniq_challenge_employee"
            )
        ]

    def __str__(self):
        return f"{self.employee} @ {self.challenge} [{self.status}]"
