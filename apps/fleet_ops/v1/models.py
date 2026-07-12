from django.conf import settings
from django.db import models

from apps.core.v1.enums import SourceType
from apps.core.v1.models import BaseModel


class Vehicle(BaseModel):
    class VehicleType(models.TextChoices):
        TRUCK = "TRUCK", "Truck"
        CAR = "CAR", "Car"
        VAN = "VAN", "Van"
        FORKLIFT = "FORKLIFT", "Forklift"

    registration_no = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    vehicle_type = models.CharField(max_length=16, choices=VehicleType.choices)
    fuel_type = models.CharField(
        max_length=20,
        choices=[
            (SourceType.DIESEL, "Diesel"),
            (SourceType.PETROL, "Petrol"),
            (SourceType.CNG, "CNG"),
            (SourceType.ELECTRICITY, "Electric"),
        ],
    )
    department = models.ForeignKey(
        "environmental_v1.Department", on_delete=models.PROTECT, related_name="vehicles"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("registration_no",)

    def __str__(self):
        return f"{self.name} ({self.registration_no})"


class FleetLog(BaseModel):
    """A fuel-consumption event. Saving one auto-creates a CarbonTransaction."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="logs")
    log_date = models.DateField()
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fuel_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-log_date",)

    def __str__(self):
        return f"{self.vehicle.registration_no} — {self.fuel_quantity} on {self.log_date}"
