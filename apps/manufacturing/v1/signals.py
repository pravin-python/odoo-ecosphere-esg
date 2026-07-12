from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.v1.enums import SourceType
from apps.environmental.v1.services import record_emission

from .models import ResourceUsage


@receiver(post_save, sender=ResourceUsage, dispatch_uid="resource_usage_emission")
def create_carbon_transactions(sender, instance, created, **kwargs):
    """Resource consumption -> CO2e; any waste is also recorded as its own line."""
    if not created:
        return

    department = instance.production_order.department
    record_emission(
        department=department,
        source_type=instance.resource_type,
        quantity=instance.quantity,
        occurred_on=instance.production_order.production_date,
        source_object=instance,
    )
    if instance.waste_generated_kg:
        record_emission(
            department=department,
            source_type=SourceType.WASTE,
            quantity=instance.waste_generated_kg,
            occurred_on=instance.production_order.production_date,
            source_object=instance,
        )
