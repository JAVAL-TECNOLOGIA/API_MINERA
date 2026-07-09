from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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
    RequerimientoProducto,
    RequerimientoRubro,
    Sucursal,
    Trabajador,
    Turno,
    UnidadMedida,
    Zona,
)
from .serializers import (
    AreaSerializer,
    CargoSerializer,
    ClimaSerializer,
    EmpresaSerializer,
    EquipoSerializer,
    ExplosivoSerializer,
    GrupoPerforacionIntegranteSerializer,
    GrupoPerforacionSerializer,
    GuardiaSerializer,
    InsumoAccesorioSerializer,
    LaborFrenteSerializer,
    LaborSerializer,
    NivelSerializer,
    ProductoSerializer,
    RequerimientoProductoSerializer,
    RequerimientoRubroSerializer,
    SucursalSerializer,
    TrabajadorSerializer,
    TurnoSerializer,
    UnidadMedidaSerializer,
    ZonaSerializer,
)


class ActiveCatalogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    ordering = ("codigo",)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request
        include_inactive = (
            request.query_params.get("include_inactive", "").lower()
            in {"1", "true", "yes"}
            and (request.user.is_staff or request.user.is_superuser)
        )

        if not include_inactive:
            queryset = queryset.filter(is_active=True, deleted_at__isnull=True)

        updated_since = request.query_params.get("updated_since")
        if updated_since:
            parsed = parse_datetime(updated_since)
            if parsed:
                queryset = queryset.filter(updated_at__gte=parsed)

        return queryset.order_by(*self.ordering)


class AreaViewSet(ActiveCatalogViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer


class GuardiaViewSet(ActiveCatalogViewSet):
    queryset = Guardia.objects.all()
    serializer_class = GuardiaSerializer


class TurnoViewSet(ActiveCatalogViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer


class ClimaViewSet(ActiveCatalogViewSet):
    queryset = Clima.objects.all()
    serializer_class = ClimaSerializer


class EmpresaViewSet(ActiveCatalogViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer


class CargoViewSet(ActiveCatalogViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer


class TrabajadorViewSet(ActiveCatalogViewSet):
    queryset = Trabajador.objects.select_related("cargo", "empresa")
    serializer_class = TrabajadorSerializer
    ordering = ("apellidos", "nombres", "codigo")


class ZonaViewSet(ActiveCatalogViewSet):
    queryset = Zona.objects.all()
    serializer_class = ZonaSerializer


class NivelViewSet(ActiveCatalogViewSet):
    queryset = Nivel.objects.all()
    serializer_class = NivelSerializer
    ordering = ("numero", "codigo")


class LaborViewSet(ActiveCatalogViewSet):
    queryset = Labor.objects.select_related("zona", "nivel")
    serializer_class = LaborSerializer
    ordering = ("titulo", "codigo")


class LaborFrenteViewSet(ActiveCatalogViewSet):
    queryset = LaborFrente.objects.select_related("labor", "zona", "nivel")
    serializer_class = LaborFrenteSerializer
    ordering = ("titulo", "codigo")


class GrupoPerforacionViewSet(ActiveCatalogViewSet):
    queryset = GrupoPerforacion.objects.all()
    serializer_class = GrupoPerforacionSerializer


class GrupoPerforacionIntegranteViewSet(ActiveCatalogViewSet):
    queryset = GrupoPerforacionIntegrante.objects.select_related("grupo", "trabajador")
    serializer_class = GrupoPerforacionIntegranteSerializer
    ordering = ("grupo_id", "trabajador_id")


class ProductoViewSet(ActiveCatalogViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class UnidadMedidaViewSet(ActiveCatalogViewSet):
    queryset = UnidadMedida.objects.all()
    serializer_class = UnidadMedidaSerializer


class SucursalViewSet(ActiveCatalogViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer


class RequerimientoRubroViewSet(ActiveCatalogViewSet):
    queryset = RequerimientoRubro.objects.all()
    serializer_class = RequerimientoRubroSerializer


class RequerimientoProductoViewSet(ActiveCatalogViewSet):
    queryset = RequerimientoProducto.objects.select_related("rubro", "unidad_medida")
    serializer_class = RequerimientoProductoSerializer
    ordering = ("seccion", "nombre", "codigo")


class ExplosivoViewSet(ActiveCatalogViewSet):
    queryset = Explosivo.objects.select_related("unidad_medida")
    serializer_class = ExplosivoSerializer


class InsumoAccesorioViewSet(ActiveCatalogViewSet):
    queryset = InsumoAccesorio.objects.select_related("unidad_medida")
    serializer_class = InsumoAccesorioSerializer


class EquipoViewSet(ActiveCatalogViewSet):
    queryset = Equipo.objects.select_related("empresa")
    serializer_class = EquipoSerializer
