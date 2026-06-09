from django.contrib import admin

from .models import AsignacionCartillaUsuario, TipoCartilla


@admin.register(TipoCartilla)
class TipoCartillaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "version", "is_active", "updated_at")
    search_fields = ("codigo", "nombre")
    list_filter = ("is_active",)


@admin.register(AsignacionCartillaUsuario)
class AsignacionCartillaUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "tipo_cartilla", "estado", "assigned_at", "updated_at")
    search_fields = ("user__username", "tipo_cartilla__codigo", "tipo_cartilla__nombre")
    list_filter = ("estado", "tipo_cartilla")
