from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "department", "is_staff")
    list_filter = ("role", "is_staff", "is_active", "department")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("ESG profile", {"fields": ("role", "department", "phone")}),
    )
