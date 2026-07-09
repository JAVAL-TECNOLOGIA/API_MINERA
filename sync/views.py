from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from auth_api.serializers import CurrentUserSerializer, get_user_roles
from cartillas.serializers import TipoCartillaSerializer
from cartillas.views import tipos_cartilla_for_user
from catalogos.models import (
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
from catalogos.serializers import (
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
from sync.mina_sync import MinaCartillaSyncService
from sync.serializers import (
    CartillaOperacionMinaSyncRequestSerializer,
    CartillaOperacionMinaSyncResponseSerializer,
)


CATALOG_BOOTSTRAP = {
    "areas": (Area, AreaSerializer, ("codigo",)),
    "guardias": (Guardia, GuardiaSerializer, ("codigo",)),
    "turnos": (Turno, TurnoSerializer, ("codigo",)),
    "climas": (Clima, ClimaSerializer, ("codigo",)),
    "empresas": (Empresa, EmpresaSerializer, ("codigo",)),
    "cargos": (Cargo, CargoSerializer, ("codigo",)),
    "trabajadores": (Trabajador, TrabajadorSerializer, ("apellidos", "nombres", "codigo")),
    "zonas": (Zona, ZonaSerializer, ("codigo",)),
    "niveles": (Nivel, NivelSerializer, ("numero", "codigo")),
    "labores": (Labor, LaborSerializer, ("titulo", "codigo")),
    "labores_frente": (LaborFrente, LaborFrenteSerializer, ("titulo", "codigo")),
    "grupos_perforacion": (GrupoPerforacion, GrupoPerforacionSerializer, ("codigo",)),
    "grupos_perforacion_integrantes": (
        GrupoPerforacionIntegrante,
        GrupoPerforacionIntegranteSerializer,
        ("grupo_id", "trabajador_id"),
    ),
    "productos": (Producto, ProductoSerializer, ("codigo",)),
    "sucursales": (Sucursal, SucursalSerializer, ("codigo",)),
    "requerimiento_rubros": (RequerimientoRubro, RequerimientoRubroSerializer, ("codigo",)),
    "requerimiento_productos": (
        RequerimientoProducto,
        RequerimientoProductoSerializer,
        ("seccion", "nombre", "codigo"),
    ),
    "unidades_medida": (UnidadMedida, UnidadMedidaSerializer, ("codigo",)),
    "explosivos": (Explosivo, ExplosivoSerializer, ("codigo",)),
    "insumos_accesorios": (InsumoAccesorio, InsumoAccesorioSerializer, ("codigo",)),
    "equipos": (Equipo, EquipoSerializer, ("codigo",)),
}


@api_view(["GET"])
@permission_classes([AllowAny])
def module_status(request):
    return Response({"module": "sync", "status": "ready"})


def permissions_for_roles(user, roles):
    is_admin = user.is_superuser or "admin" in roles
    return {
        "can_create_cartilla": is_admin
        or bool({"operador", "supervisor"} & set(roles)),
        "can_review_cartilla": is_admin
        or bool({"supervisor", "revisor"} & set(roles)),
        "can_admin_catalogos": is_admin,
    }


def active_catalog_queryset(model, updated_since=None, ordering=("codigo",)):
    queryset = model.objects.filter(is_active=True, deleted_at__isnull=True)
    if updated_since:
        parsed = (
            parse_datetime(updated_since)
            if isinstance(updated_since, str)
            else updated_since
        )
        if parsed:
            queryset = queryset.filter(updated_at__gte=parsed)
    return queryset.order_by(*ordering)


def catalog_payload(updated_since=None):
    payload = {}
    for key, (model, serializer_class, ordering) in CATALOG_BOOTSTRAP.items():
        queryset = active_catalog_queryset(model, updated_since, ordering)
        payload[key] = serializer_class(queryset, many=True).data
    return payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mobile_bootstrap(request):
    updated_since = request.query_params.get("updated_since")
    if updated_since:
        updated_since = parse_datetime(updated_since)

    roles = get_user_roles(request.user)
    tipos_cartilla = tipos_cartilla_for_user(request.user, updated_since=updated_since)

    return Response(
        {
            "server_time": timezone.now(),
            "user": CurrentUserSerializer(request.user).data,
            "roles": roles,
            "permissions": permissions_for_roles(request.user, roles),
            "tipos_cartilla": TipoCartillaSerializer(tipos_cartilla, many=True).data,
            "catalogos": catalog_payload(updated_since=updated_since),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_cartilla_operacion_mina(request):
    serializer = CartillaOperacionMinaSyncRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    result = MinaCartillaSyncService(
        user=request.user,
        validated_data=serializer.validated_data,
    ).sync()
    response = CartillaOperacionMinaSyncResponseSerializer(result)
    return Response(response.data)
