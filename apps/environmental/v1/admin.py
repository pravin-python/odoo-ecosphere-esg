from django.contrib import admin

from .models import (
    CarbonTransaction,
    Department,
    DepartmentScore,
    EmissionFactor,
    SustainabilityGoal,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "manager", "total_co2e_kg", "esg_score", "is_active")
    search_fields = ("name", "code")


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "unit", "factor_value", "effective_from", "is_active")
    list_filter = ("source_type", "is_active")


@admin.register(CarbonTransaction)
class CarbonTransactionAdmin(admin.ModelAdmin):
    list_display = ("department", "source_type", "quantity", "co2e_kg", "occurred_on")
    list_filter = ("source_type", "occurred_on")
    date_hierarchy = "occurred_on"
    readonly_fields = ("co2e_kg",)


@admin.register(SustainabilityGoal)
class SustainabilityGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "metric", "target_value", "target_date", "status")
    list_filter = ("metric", "status")


@admin.register(DepartmentScore)
class DepartmentScoreAdmin(admin.ModelAdmin):
    list_display = ("department", "period_year", "environmental_score", "social_score",
                    "governance_score", "total_score", "computed_at")
    list_filter = ("period_year",)
    readonly_fields = ("computed_at",)
