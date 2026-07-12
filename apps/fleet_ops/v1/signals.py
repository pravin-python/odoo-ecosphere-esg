from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.environmental.v1.services import record_emission

from .models import FleetLog


@receiver(post_save, sender=FleetLog, dispatch_uid="fleet_log_emission")
def create_carbon_transaction(sender, instance, created, **kwargs):
    """Fuel logged -> CO2e recorded automatically. No manual entry."""
    if not created:
        return
    record_emission(
        department=instance.vehicle.department,
        source_type=instance.vehicle.fuel_type,
        quantity=instance.fuel_quantity,
        occurred_on=instance.log_date,
        created_by=instance.logged_by,
        source_object=instance,
    )
