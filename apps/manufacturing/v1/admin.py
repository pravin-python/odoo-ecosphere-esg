from django.contrib import admin

from .models import ProductionOrder, ResourceUsage


class ResourceUsageInline(admin.TabularInline):
    model = ResourceUsage
    extra = 1


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "product_name", "department", "quantity_produced",
                    "production_date", "status")
    list_filter = ("status", "production_date")
    inlines = [ResourceUsageInline]


@admin.register(ResourceUsage)
class ResourceUsageAdmin(admin.ModelAdmin):
    list_display = ("production_order", "resource_type", "quantity", "unit", "waste_generated_kg")
    list_filter = ("resource_type",)
