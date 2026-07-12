from django.conf import settings
from django.db import models

from apps.core.v1.enums import ApprovalStatus
from apps.core.v1.models import BaseModel


class CSRActivity(BaseModel):
    class Category(models.TextChoices):
        ENVIRONMENT = "ENVIRONMENT", "Environment"
        COMMUNITY = "COMMUNITY", "Community"
        EDUCATION = "EDUCATION", "Education"
        HEALTH = "HEALTH", "Health"

    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=16, choices=Category.choices)
    category_ref = models.ForeignKey(
        "system_core_v1.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"type": "CSR_ACTIVITY"},
        related_name="csr_activities",
        help_text="Shared master category (Settings → Categories).",
    )
    xp_reward = models.PositiveIntegerField(default=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-start_date",)
        verbose_name = "CSR Activity"
        verbose_name_plural = "CSR Activities"

    def __str__(self):
        return self.title


def evidence_upload_path(instance, filename):
    return f"csr_evidence/{instance.activity_id}/{filename}"


class EmployeeParticipation(BaseModel):
    """An employee's claim of participation, gated by manager approval.

    Evidence upload is mandatory when GlobalConfiguration.strict_evidence_required
    is on (enforced in the serializer/form layer)."""

    activity = models.ForeignKey(
        CSRActivity, on_delete=models.CASCADE, related_name="participations"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="csr_participations"
    )
    proof_file = models.FileField(upload_to=evidence_upload_path, blank=True)
    status = models.CharField(
        max_length=12, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING, db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_participations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.CharField(max_length=255, blank=True)
    xp_awarded = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "employee"], name="uniq_activity_employee"
            )
        ]

    def __str__(self):
        return f"{self.employee} @ {self.activity} [{self.status}]"
