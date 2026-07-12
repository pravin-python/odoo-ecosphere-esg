from django.contrib import admin

from .models import FleetLog, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_no", "vehicle_type", "fuel_type", "department", "is_active")
    list_filter = ("vehicle_type", "fuel_type", "is_active")
    search_fields = ("name", "registration_no")


@admin.register(FleetLog)
class FleetLogAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "log_date", "fuel_quantity", "distance_km", "logged_by")
    list_filter = ("log_date",)
    date_hierarchy = "log_date"
