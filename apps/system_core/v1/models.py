from django.core.cache import cache
from django.db import models

from apps.core.v1.models import BaseModel, TimeStampedModel


class Category(BaseModel):
    """Shared taxonomy used across the Social and Gamification modules.

    A single master table (rather than per-module choice enums) so CSR Activity
    and Challenge categories can be managed from one Settings screen and reused
    in report filters.
    """

    class Type(models.TextChoices):
        CSR_ACTIVITY = "CSR_ACTIVITY", "CSR Activity"
        CHALLENGE = "CHALLENGE", "Challenge"

    name = models.CharField(max_length=120)
    type = models.CharField(max_length=16, choices=Type.choices, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("type", "name")
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type"],
                condition=models.Q(is_deleted=False),
                name="uniq_category_name_per_type",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class ProductESGProfile(BaseModel):
    """ESG attributes attached to a product/SKU, used for product-level carbon
    accounting and supplier/packaging sustainability metrics."""

    name = models.CharField(max_length=160)
    sku = models.CharField(max_length=64, unique=True)
    carbon_footprint_kg = models.DecimalField(
        max_digits=12, decimal_places=3, default=0,
        help_text="Embedded kg CO2e per unit of this product.",
    )
    recyclable = models.BooleanField(default=False)
    ethical_sourcing_score = models.PositiveSmallIntegerField(
        default=0, help_text="Supplier ethics score 0-100."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Product ESG Profile"

    def __str__(self):
        return f"{self.name} [{self.sku}]"


class GlobalConfiguration(TimeStampedModel):
    """Platform-wide feature toggles, enforced as a single-row singleton.

    Other apps call ``GlobalConfiguration.load()`` before running automation so
    behaviour can be flipped org-wide without a deploy.
    """

    CACHE_KEY = "global_configuration"

    auto_emission_enabled = models.BooleanField(
        default=True, help_text="Auto-generate carbon transactions from ERP records."
    )
    strict_evidence_required = models.BooleanField(
        default=True, help_text="Require proof upload before CSR participation can be approved."
    )
    badge_auto_award_enabled = models.BooleanField(
        default=True, help_text="Auto-assign badges the moment an Unlock Rule is satisfied."
    )
    current_reporting_year = models.PositiveIntegerField(default=2026)
    default_carbon_reduction_target = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.0, help_text="Target % reduction."
    )

    # Overall ESG Score = weighted average of the three pillar scores.
    # Defaults match the challenge brief (E 40% / S 30% / G 30%); configurable per org.
    weight_environmental = models.PositiveSmallIntegerField(
        default=40, help_text="Environmental weight (%) in the Overall ESG Score."
    )
    weight_social = models.PositiveSmallIntegerField(
        default=30, help_text="Social weight (%) in the Overall ESG Score."
    )
    weight_governance = models.PositiveSmallIntegerField(
        default=30, help_text="Governance weight (%) in the Overall ESG Score."
    )

    @property
    def weight_total(self) -> int:
        return self.weight_environmental + self.weight_social + self.weight_governance

    class Meta:
        verbose_name = "Global Configuration"
        verbose_name_plural = "Global Configuration"

    def __str__(self):
        return "EcoSphere Global Configuration"

    def save(self, *args, **kwargs):
        self.pk = 1  # enforce singleton
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    def delete(self, *args, **kwargs):  # pragma: no cover - guard rail
        raise RuntimeError("GlobalConfiguration is a singleton and cannot be deleted.")

    @classmethod
    def load(cls):
        config = cache.get(cls.CACHE_KEY)
        if config is None:
            config, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, config)
        return config
