from django.conf import settings
from django.db import models

from apps.core.v1.enums import MeasurementUnit, SourceType
from apps.core.v1.models import BaseModel


class Vendor(BaseModel):
    name = models.CharField(max_length=160)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    esg_rating = models.PositiveSmallIntegerField(
        default=0, help_text="Supplier sustainability score 0-100."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class PurchaseOrder(BaseModel):
    """A procurement of energy/materials. Emitting items auto-create CO2e."""

    class ItemType(models.TextChoices):
        ELECTRICITY = SourceType.ELECTRICITY, "Electricity"
        NATURAL_GAS = SourceType.NATURAL_GAS, "Natural Gas"
        WATER = SourceType.WATER, "Water"
        RAW_MATERIAL = SourceType.RAW_MATERIAL, "Raw Material"

    reference = models.CharField(max_length=40, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="purchase_orders")
    department = models.ForeignKey(
        "environmental_v1.Department", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit = models.CharField(max_length=20, choices=MeasurementUnit.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    order_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-order_date",)

    def __str__(self):
        return f"{self.reference} — {self.get_item_type_display()}"
