from django.contrib import admin

from .models import CSRActivity, EmployeeParticipation


@admin.register(CSRActivity)
class CSRActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "xp_reward", "start_date", "end_date", "is_active")
    list_filter = ("category", "is_active")


@admin.register(EmployeeParticipation)
class EmployeeParticipationAdmin(admin.ModelAdmin):
    list_display = ("employee", "activity", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    actions = ["approve_selected"]

    @admin.action(description="Approve selected participations")
    def approve_selected(self, request, queryset):
        from django.utils import timezone

        from apps.core.v1.enums import ApprovalStatus

        for participation in queryset.exclude(status=ApprovalStatus.APPROVED):
            participation.status = ApprovalStatus.APPROVED
            participation.reviewed_by = request.user
            participation.reviewed_at = timezone.now()
            participation.save()  # triggers XP award signal
