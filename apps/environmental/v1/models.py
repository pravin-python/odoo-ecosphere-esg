from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.core.v1.enums import MeasurementUnit, SourceType
from apps.core.v1.models import BaseModel


class Department(BaseModel):
    """Organizational unit; carries the aggregated ESG figures shown on dashboards."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_departments"
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
    )
    total_co2e_kg = models.DecimalField(max_digits=16, decimal_places=3, default=0)
    esg_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} [{self.code}]"


class EmissionFactor(BaseModel):
    """Admin-defined multiplier, e.g. 1 L Diesel = 2.68 kg CO2e."""

    name = models.CharField(max_length=120)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, db_index=True)
    unit = models.CharField(max_length=20, choices=MeasurementUnit.choices)
    factor_value = models.DecimalField(
        max_digits=12, decimal_places=4, help_text="kg CO2e emitted per 1 unit of source."
    )
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("source_type", "-effective_from")
        constraints = [
            models.UniqueConstraint(
                fields=["source_type"],
                condition=models.Q(is_active=True, is_deleted=False),
                name="uniq_active_factor_per_source",
            )
        ]

    def __str__(self):
        return f"{self.get_source_type_display()}: {self.factor_value} kg CO2e/{self.unit}"


class CarbonTransaction(BaseModel):
    """Central, auto-generated CO2e ledger. Rows are created by signals, not humans."""

    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="carbon_transactions"
    )
    source_type = models.CharField(max_length=20, choices=SourceType.choices, db_index=True)
    emission_factor = models.ForeignKey(
        EmissionFactor, on_delete=models.PROTECT, related_name="transactions"
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    co2e_kg = models.DecimalField(max_digits=16, decimal_places=3)
    occurred_on = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Generic link back to the originating ERP record (FleetLog / PurchaseOrder / ...).
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    source_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ("-occurred_on", "-created_at")
        indexes = [
            models.Index(fields=["department", "occurred_on"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.co2e_kg} kg CO2e — {self.department.code} ({self.source_type})"


class SustainabilityGoal(BaseModel):
    class Metric(models.TextChoices):
        CARBON_REDUCTION = "CARBON_REDUCTION", "Carbon Reduction (%)"
        ENERGY_REDUCTION = "ENERGY_REDUCTION", "Energy Reduction (%)"
        WASTE_REDUCTION = "WASTE_REDUCTION", "Waste Reduction (%)"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ACHIEVED = "ACHIEVED", "Achieved"
        MISSED = "MISSED", "Missed"

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="goals",
        help_text="Null = company-wide goal.",
    )
    title = models.CharField(max_length=160)
    metric = models.CharField(max_length=32, choices=Metric.choices)
    baseline_value = models.DecimalField(max_digits=14, decimal_places=3)
    target_value = models.DecimalField(max_digits=14, decimal_places=3)
    target_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ("target_date",)

    def __str__(self):
        return self.title


class DepartmentScore(BaseModel):
    """Aggregated ESG performance snapshot for a department in a reporting year.

    Written by the scoring engine (``apps.environmental.v1.scoring``). Keeping a
    row per (department, period_year) gives history for trend charts instead of
    overwriting a single figure."""

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="scores"
    )
    period_year = models.PositiveIntegerField(db_index=True)
    environmental_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    social_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    governance_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("department", "-period_year")
        constraints = [
            models.UniqueConstraint(
                fields=["department", "period_year"], name="uniq_department_period_score"
            )
        ]

    def __str__(self):
        return f"{self.department.code} {self.period_year}: {self.total_score}"
