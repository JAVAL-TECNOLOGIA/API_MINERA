from django.urls import path

from .views import module_status, sync_cartilla_operacion_mina


urlpatterns = [
    path("", module_status, name="sync_status"),
    path(
        "cartillas-operacion-mina/",
        sync_cartilla_operacion_mina,
        name="sync_cartilla_operacion_mina",
    ),
]
