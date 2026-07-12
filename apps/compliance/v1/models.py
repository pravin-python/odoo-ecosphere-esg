from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.v1.enums import ESGPillar, Severity
from apps.core.v1.managers import SoftDeleteManager, SoftDeleteQuerySet
from apps.core.v1.models import BaseModel


class ESGPolicy(BaseModel):
    title = models.CharField(max_length=200)
    pillar = models.CharField(max_length=1, choices=ESGPillar.choices)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=20, default="1.0")
    effective_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)
        verbose_name = "ESG Policy"
        verbose_name_plural = "ESG Policies"

    def __str__(self):
        return f"{self.title} v{self.version}"


class PolicyAcknowledgement(BaseModel):
    """Record of an employee accepting a specific ESG policy version.

    One row per (policy, employee). ``acknowledged_at`` is null until the
    employee actually accepts — pending rows drive acknowledgement reminders."""

    policy = models.ForeignKey(
        ESGPolicy, on_delete=models.CASCADE, related_name="acknowledgements"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="policy_acknowledgements"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["policy", "employee"], name="uniq_policy_employee_ack"
            )
        ]

    def __str__(self):
        state = "acknowledged" if self.acknowledged_at else "pending"
        return f"{self.employee} — {self.policy.title} [{state}]"

    @property
    def is_acknowledged(self) -> bool:
        return self.acknowledged_at is not None


class Audit(BaseModel):
    class AuditType(models.TextChoices):
        INTERNAL = "INTERNAL", "Internal"
        EXTERNAL = "EXTERNAL", "External"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    audit_type = models.CharField(max_length=10, choices=AuditType.choices)
    department = models.ForeignKey(
        "environmental_v1.Department", on_delete=models.PROTECT, related_name="audits"
    )
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    scheduled_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)

    class Meta:
        ordering = ("-scheduled_date",)

    def __str__(self):
        return f"{self.title} ({self.audit_type})"


class ComplianceIssueQuerySet(SoftDeleteQuerySet):
    def open(self):
        return self.exclude(status=ComplianceIssue.Status.RESOLVED)

    def overdue(self):
        """Open issues whose due date has passed — the source of dashboard red flags."""
        return self.open().filter(due_date__lt=timezone.now().date())


class ComplianceIssueManager(SoftDeleteManager):
    def get_queryset(self):
        return ComplianceIssueQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def overdue(self):
        return self.get_queryset().overdue()


class ComplianceIssue(BaseModel):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"

    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="issues")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_issues"
    )
    due_date = models.DateField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    objects = ComplianceIssueManager()

    class Meta:
        ordering = ("due_date",)
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return f"{self.title} [{self.severity}]"

    @property
    def is_overdue(self) -> bool:
        """Computed live — no cron needed to keep an 'overdue' column in sync."""
        return self.status != self.Status.RESOLVED and self.due_date < timezone.now().date()
