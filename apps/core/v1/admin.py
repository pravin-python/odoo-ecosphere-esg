from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "method", "path", "status_code", "ip_address")
    list_filter = ("method", "status_code")
    search_fields = ("path", "actor__username", "ip_address")
    readonly_fields = ("actor", "method", "path", "status_code", "ip_address", "user_agent",
                       "created_at", "updated_at")

    def has_add_permission(self, request):
        return False  # audit trail is written by middleware only
