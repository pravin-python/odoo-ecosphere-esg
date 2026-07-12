"""Single source of truth for turning an operational quantity into CO2e.

Every ERP app's signal funnels through :func:`record_emission` so the carbon
maths lives in exactly one place — not copy-pasted across fleet/procurement/
manufacturing.
"""
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from django.utils import timezone

from .models import CarbonTransaction, Department, EmissionFactor


class EmissionError(Exception):
    pass


def _auto_emission_enabled() -> bool:
    from apps.system_core.v1.models import GlobalConfiguration

    return GlobalConfiguration.load().auto_emission_enabled


def record_emission(*, department, source_type, quantity, occurred_on=None,
                    created_by=None, source_object=None):
    """Look up the active emission factor and write a CarbonTransaction.

    Returns the created transaction, or ``None`` when auto-emission is disabled
    or no active factor exists for ``source_type`` (we skip silently rather than
    block the underlying ERP save).
    """
    if not _auto_emission_enabled():
        return None

    factor = (
        EmissionFactor.objects.filter(source_type=source_type, is_active=True)
        .order_by("-effective_from")
        .first()
    )
    if factor is None:
        return None

    quantity = Decimal(str(quantity))
    co2e = (quantity * factor.factor_value).quantize(Decimal("0.001"))

    txn = CarbonTransaction.objects.create(
        department=department,
        source_type=source_type,
        emission_factor=factor,
        quantity=quantity,
        co2e_kg=co2e,
        occurred_on=occurred_on or timezone.now().date(),
        created_by=created_by,
        content_type=ContentType.objects.get_for_model(source_object) if source_object else None,
        object_id=getattr(source_object, "pk", None),
    )
    # Atomic increment — safe under concurrent ERP saves.
    Department.all_objects.filter(pk=department.pk).update(
        total_co2e_kg=F("total_co2e_kg") + co2e
    )
    return txn
