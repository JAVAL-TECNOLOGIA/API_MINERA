from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AreaViewSet,
    CargoViewSet,
    ClimaViewSet,
    EmpresaViewSet,
    EquipoViewSet,
    ExplosivoViewSet,
    GrupoPerforacionIntegranteViewSet,
    GrupoPerforacionViewSet,
    GuardiaViewSet,
    InsumoAccesorioViewSet,
    LaborFrenteViewSet,
    LaborViewSet,
    NivelViewSet,
    ProductoViewSet,
    TrabajadorViewSet,
    TurnoViewSet,
    UnidadMedidaViewSet,
    ZonaViewSet,
)


router = DefaultRouter()
router.register("areas", AreaViewSet, basename="catalogos-areas")
router.register("guardias", GuardiaViewSet, basename="catalogos-guardias")
router.register("turnos", TurnoViewSet, basename="catalogos-turnos")
router.register("climas", ClimaViewSet, basename="catalogos-climas")
router.register("empresas", EmpresaViewSet, basename="catalogos-empresas")
router.register("cargos", CargoViewSet, basename="catalogos-cargos")
router.register("trabajadores", TrabajadorViewSet, basename="catalogos-trabajadores")
router.register("zonas", ZonaViewSet, basename="catalogos-zonas")
router.register("niveles", NivelViewSet, basename="catalogos-niveles")
router.register("labores", LaborViewSet, basename="catalogos-labores")
router.register("labores-frente", LaborFrenteViewSet, basename="catalogos-labores-frente")
router.register(
    "grupos-perforacion",
    GrupoPerforacionViewSet,
    basename="catalogos-grupos-perforacion",
)
router.register(
    "grupos-perforacion-integrantes",
    GrupoPerforacionIntegranteViewSet,
    basename="catalogos-grupos-perforacion-integrantes",
)
router.register("productos", ProductoViewSet, basename="catalogos-productos")
router.register(
    "unidades-medida",
    UnidadMedidaViewSet,
    basename="catalogos-unidades-medida",
)
router.register("explosivos", ExplosivoViewSet, basename="catalogos-explosivos")
router.register(
    "insumos-accesorios",
    InsumoAccesorioViewSet,
    basename="catalogos-insumos-accesorios",
)
router.register("equipos", EquipoViewSet, basename="catalogos-equipos")

urlpatterns = [
    path("", include(router.urls)),
]
