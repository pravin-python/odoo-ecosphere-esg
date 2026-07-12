from django.contrib import admin

from .models import PurchaseOrder, Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "esg_rating", "is_active")
    search_fields = ("name",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "vendor", "department", "item_type", "quantity", "order_date")
    list_filter = ("item_type", "order_date")
    date_hierarchy = "order_date"
