from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User, UserProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Mina Carolina", {"fields": ("dni", "phone", "deleted_at")}),
        ("Auditoria", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "dni",
        "is_staff",
        "is_active",
    )
    search_fields = ("username", "email", "first_name", "last_name", "dni")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "updated_at")
    search_fields = ("code", "name")
    list_filter = ("is_active",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "empresa", "is_active", "updated_at")
    search_fields = ("user__username", "role__code", "role__name")
    list_filter = ("role", "empresa", "is_active")
