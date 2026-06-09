from django.contrib import admin

from .models import (
    CartillaAccionCorrectiva,
    CartillaAvance,
    CartillaEquipo,
    CartillaExtraccionAcarreo,
    CartillaOperacionMina,
    CartillaPerforacionExplosivo,
    CartillaPerforacionInsumo,
    CartillaPerforacionVoladura,
    CartillaPersonal,
    CartillaWorkflowLog,
)


@admin.register(CartillaOperacionMina)
class CartillaOperacionMinaAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_operacion",
        "turno",
        "guardia",
        "area",
        "user",
        "estado_workflow",
        "sync_status",
        "updated_at",
    )
    search_fields = ("client_record_id", "user__username")
    list_filter = ("estado_workflow", "sync_status", "turno", "guardia", "area")


class CartillaRowAdmin(admin.ModelAdmin):
    list_display = ("cartilla", "row_key", "updated_at")
    search_fields = ("row_key",)


admin.site.register(CartillaPerforacionVoladura, CartillaRowAdmin)
admin.site.register(CartillaExtraccionAcarreo, CartillaRowAdmin)
admin.site.register(CartillaPersonal, CartillaRowAdmin)
admin.site.register(CartillaEquipo, CartillaRowAdmin)
admin.site.register(CartillaAvance, CartillaRowAdmin)
admin.site.register(CartillaAccionCorrectiva, CartillaRowAdmin)


@admin.register(CartillaPerforacionExplosivo)
class CartillaPerforacionExplosivoAdmin(admin.ModelAdmin):
    list_display = ("perforacion", "row_key", "explosivo", "cantidad", "unidad_medida")
    search_fields = ("row_key",)


@admin.register(CartillaPerforacionInsumo)
class CartillaPerforacionInsumoAdmin(admin.ModelAdmin):
    list_display = ("perforacion", "row_key", "insumo", "cantidad", "unidad_medida")
    search_fields = ("row_key",)


@admin.register(CartillaWorkflowLog)
class CartillaWorkflowLogAdmin(admin.ModelAdmin):
    list_display = ("cartilla", "from_state", "to_state", "action", "created_by", "created_at")
    search_fields = ("action", "comment")
    list_filter = ("to_state", "action")
