from django.contrib import admin
from django.utils.html import format_html

from .models import Audit, ComplianceIssue, ESGPolicy, PolicyAcknowledgement


@admin.register(ESGPolicy)
class ESGPolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "pillar", "version", "effective_date", "is_active")
    list_filter = ("pillar", "is_active")


@admin.register(PolicyAcknowledgement)
class PolicyAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ("policy", "employee", "acknowledged_at", "is_acknowledged")
    list_filter = ("policy",)
    search_fields = ("employee__username", "policy__title")


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("title", "audit_type", "department", "auditor", "scheduled_date", "status")
    list_filter = ("audit_type", "status")


@admin.register(ComplianceIssue)
class ComplianceIssueAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "owner", "due_date", "status", "overdue_flag")
    list_filter = ("severity", "status")

    @admin.display(description="Overdue")
    def overdue_flag(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color:red;font-weight:bold;">OVERDUE</span>')
        return "—"
