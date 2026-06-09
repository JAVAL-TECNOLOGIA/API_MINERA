from django.contrib import admin

from .models import (
    Area,
    Cargo,
    Clima,
    Empresa,
    Equipo,
    Explosivo,
    GrupoPerforacion,
    GrupoPerforacionIntegrante,
    Guardia,
    InsumoAccesorio,
    Labor,
    LaborFrente,
    Nivel,
    Producto,
    Trabajador,
    Turno,
    UnidadMedida,
    Zona,
)


class CatalogoBaseAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "is_active", "updated_at")
    search_fields = ("codigo", "nombre")
    list_filter = ("is_active",)


admin.site.register(Area, CatalogoBaseAdmin)
admin.site.register(Guardia, CatalogoBaseAdmin)
admin.site.register(Clima, CatalogoBaseAdmin)
admin.site.register(Cargo, CatalogoBaseAdmin)
admin.site.register(Producto, CatalogoBaseAdmin)
admin.site.register(UnidadMedida, CatalogoBaseAdmin)


@admin.register(Turno)
class TurnoAdmin(CatalogoBaseAdmin):
    list_display = (
        "codigo",
        "nombre",
        "hora_inicio",
        "hora_fin",
        "cruza_medianoche",
        "is_active",
    )


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "ruc", "razon_social", "is_active", "updated_at")
    search_fields = ("codigo", "ruc", "razon_social")
    list_filter = ("is_active",)


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = (
        "dni",
        "apellidos",
        "nombres",
        "cargo",
        "empresa",
        "es_supervisor",
        "es_operador",
        "is_active",
    )
    search_fields = ("codigo", "dni", "nombres", "apellidos")
    list_filter = (
        "cargo",
        "empresa",
        "es_ingeniero_minero",
        "es_supervisor",
        "es_operador",
        "is_active",
    )


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "letra", "nombre", "is_active", "updated_at")
    search_fields = ("codigo", "letra", "nombre")
    list_filter = ("is_active",)


@admin.register(Nivel)
class NivelAdmin(admin.ModelAdmin):
    list_display = ("codigo", "numero", "is_active", "updated_at")
    search_fields = ("codigo", "numero")
    list_filter = ("is_active",)


@admin.register(Labor)
class LaborAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "zona", "nivel", "is_active", "updated_at")
    search_fields = ("codigo", "titulo")
    list_filter = ("zona", "nivel", "is_active")


@admin.register(LaborFrente)
class LaborFrenteAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "labor", "zona", "nivel", "is_active")
    search_fields = ("codigo", "titulo")
    list_filter = ("labor", "zona", "nivel", "is_active")


@admin.register(GrupoPerforacion)
class GrupoPerforacionAdmin(CatalogoBaseAdmin):
    pass


@admin.register(GrupoPerforacionIntegrante)
class GrupoPerforacionIntegranteAdmin(admin.ModelAdmin):
    list_display = ("grupo", "trabajador", "rol_en_grupo", "is_active")
    search_fields = ("grupo__codigo", "trabajador__dni", "trabajador__apellidos")
    list_filter = ("grupo", "is_active")


@admin.register(Explosivo)
class ExplosivoAdmin(CatalogoBaseAdmin):
    list_display = ("codigo", "nombre", "unidad_medida", "is_active", "updated_at")
    list_filter = ("unidad_medida", "is_active")


@admin.register(InsumoAccesorio)
class InsumoAccesorioAdmin(CatalogoBaseAdmin):
    list_display = ("codigo", "nombre", "unidad_medida", "is_active", "updated_at")
    list_filter = ("unidad_medida", "is_active")


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "empresa", "is_active", "updated_at")
    search_fields = ("codigo", "nombre", "tipo")
    list_filter = ("empresa", "tipo", "is_active")
