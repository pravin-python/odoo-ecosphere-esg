from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.environmental.v1.services import record_emission

from .models import PurchaseOrder


@receiver(post_save, sender=PurchaseOrder, dispatch_uid="purchase_order_emission")
def create_carbon_transaction(sender, instance, created, **kwargs):
    """Purchasing energy/materials records its embodied CO2e automatically."""
    if not created:
        return
    record_emission(
        department=instance.department,
        source_type=instance.item_type,
        quantity=instance.quantity,
        occurred_on=instance.order_date,
        created_by=instance.created_by,
        source_object=instance,
    )
