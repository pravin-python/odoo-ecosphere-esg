from django.contrib import admin

from .models import Category, GlobalConfiguration, ProductESGProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "is_active")
    list_filter = ("type", "is_active")
    search_fields = ("name",)


@admin.register(ProductESGProfile)
class ProductESGProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "carbon_footprint_kg", "recyclable",
                    "ethical_sourcing_score", "is_active")
    list_filter = ("recyclable", "is_active")
    search_fields = ("name", "sku")


@admin.register(GlobalConfiguration)
class GlobalConfigurationAdmin(admin.ModelAdmin):
    list_display = ("__str__", "auto_emission_enabled", "strict_evidence_required",
                    "badge_auto_award_enabled", "current_reporting_year")

    def has_add_permission(self, request):
        return not GlobalConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
