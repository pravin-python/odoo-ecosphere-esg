from django.conf import settings
from django.db import models

from apps.core.v1.models import BaseModel


class SavedReport(BaseModel):
    """A reusable report definition built with the Custom Report Builder.

    Stores the report type plus the chosen filters as JSON so a user can re-run
    or export the same view later without re-selecting everything."""

    class ReportType(models.TextChoices):
        ENVIRONMENTAL = "ENVIRONMENTAL", "Environmental"
        SOCIAL = "SOCIAL", "Social"
        GOVERNANCE = "GOVERNANCE", "Governance"
        ESG_SUMMARY = "ESG_SUMMARY", "ESG Summary"

    name = models.CharField(max_length=160)
    report_type = models.CharField(max_length=16, choices=ReportType.choices)
    filters = models.JSONField(
        default=dict, blank=True,
        help_text="Saved filter set: department, date_from/to, module, employee, "
                  "challenge, esg_category.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_reports"
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
