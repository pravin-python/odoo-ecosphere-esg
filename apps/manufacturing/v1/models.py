from django.db import models

from apps.core.v1.enums import MeasurementUnit, SourceType
from apps.core.v1.models import BaseModel


class ProductionOrder(BaseModel):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    reference = models.CharField(max_length=40, unique=True)
    product_name = models.CharField(max_length=160)
    department = models.ForeignKey(
        "environmental_v1.Department", on_delete=models.PROTECT, related_name="production_orders"
    )
    quantity_produced = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    production_date = models.DateField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLANNED)

    class Meta:
        ordering = ("-production_date",)

    def __str__(self):
        return f"{self.reference} — {self.product_name}"


class ResourceUsage(BaseModel):
    """Energy/water/gas consumed (and waste produced) during a production run.

    Saving a usage row auto-creates a CarbonTransaction for the resource type.
    """

    class ResourceType(models.TextChoices):
        ELECTRICITY = SourceType.ELECTRICITY, "Electricity"
        WATER = SourceType.WATER, "Water"
        NATURAL_GAS = SourceType.NATURAL_GAS, "Natural Gas"

    production_order = models.ForeignKey(
        ProductionOrder, on_delete=models.CASCADE, related_name="resource_usages"
    )
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=20, choices=MeasurementUnit.choices)
    waste_generated_kg = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_resource_type_display()} — {self.quantity} {self.unit}"
