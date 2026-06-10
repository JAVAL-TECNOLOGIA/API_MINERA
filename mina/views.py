from django.db.models import Count, Prefetch, Q
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from attachments.models import Attachment

from .models import (
    CartillaAccionCorrectiva,
    CartillaAvance,
    CartillaEquipo,
    CartillaExtraccionAcarreo,
    CartillaOperacionMina,
    CartillaPerforacionVoladura,
    CartillaPersonal,
    CartillaWorkflowLog,
)
from .serializers import CartillaMinaDetailSerializer, CartillaMinaListSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def module_status(request):
    return Response({"module": "mina", "status": "ready"})


def _base_cartilla_queryset():
    return (
        CartillaOperacionMina.objects.select_related(
            "tipo_cartilla",
            "user",
            "turno",
            "guardia",
            "area",
            "zona",
            "nivel",
            "ingeniero_minero",
            "supervisor",
            "clima",
        )
        .prefetch_related(
            Prefetch(
                "perforaciones_voladura",
                queryset=CartillaPerforacionVoladura.objects.select_related(
                    "grupo_perforacion",
                    "producto",
                    "labor_frente",
                ).prefetch_related(
                    "explosivos__explosivo",
                    "explosivos__unidad_medida",
                    "insumos__insumo",
                    "insumos__unidad_medida",
                ),
            ),
            Prefetch(
                "extracciones_acarreo",
                queryset=CartillaExtraccionAcarreo.objects.select_related(
                    "producto",
                    "equipo",
                    "operador",
                ),
            ),
            Prefetch(
                "personal",
                queryset=CartillaPersonal.objects.select_related(
                    "trabajador",
                    "cargo",
                    "empresa",
                ),
            ),
            Prefetch(
                "equipos",
                queryset=CartillaEquipo.objects.select_related("equipo", "operador"),
            ),
            Prefetch(
                "avances",
                queryset=CartillaAvance.objects.select_related("labor_frente"),
            ),
            Prefetch(
                "acciones_correctivas",
                queryset=CartillaAccionCorrectiva.objects.select_related("responsable"),
            ),
            Prefetch(
                "attachments",
                queryset=Attachment.objects.filter(deleted_at__isnull=True),
            ),
            Prefetch(
                "workflow_logs",
                queryset=CartillaWorkflowLog.objects.select_related("created_by"),
            ),
        )
        .annotate(
            attachments_count=Count(
                "attachments",
                filter=Q(attachments__deleted_at__isnull=True),
                distinct=True,
            ),
        )
    )


def _visible_cartillas(user):
    queryset = _base_cartilla_queryset()
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.filter(user=user)


def _apply_filters(queryset, request):
    params = request.query_params
    date_filters = {
        "fecha_operacion": "fecha_operacion",
        "fecha_desde": "fecha_operacion__gte",
        "fecha_hasta": "fecha_operacion__lte",
    }
    for param_name, lookup in date_filters.items():
        raw = params.get(param_name)
        if not raw:
            continue
        parsed = parse_date(raw)
        if parsed:
            queryset = queryset.filter(**{lookup: parsed})

    exact_filters = {
        "turno_id": "turno_id",
        "guardia_id": "guardia_id",
        "area_id": "area_id",
        "estado_workflow": "estado_workflow",
        "sync_status": "sync_status",
    }
    for param_name, lookup in exact_filters.items():
        value = params.get(param_name)
        if value not in (None, ""):
            queryset = queryset.filter(**{lookup: value})

    user_id = params.get("user_id")
    if user_id and (request.user.is_staff or request.user.is_superuser):
        queryset = queryset.filter(user_id=user_id)

    search = params.get("search")
    if search:
        queryset = queryset.filter(
            Q(client_record_id__icontains=search)
            | Q(zona__codigo__icontains=search)
            | Q(zona__nombre__icontains=search)
            | Q(nivel__codigo__icontains=search)
            | Q(area__codigo__icontains=search)
            | Q(area__nombre__icontains=search),
        )

    return queryset


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cartilla_list(request):
    queryset = _apply_filters(_visible_cartillas(request.user), request).order_by(
        "-fecha_operacion",
        "-updated_at",
    )
    serializer = CartillaMinaListSerializer(
        queryset,
        many=True,
        context={"request": request},
    )
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cartilla_detail(request, cartilla_id):
    cartilla = _visible_cartillas(request.user).filter(pk=cartilla_id).first()
    if cartilla is None:
        return Response(
            {"detail": "Cartilla no encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = CartillaMinaDetailSerializer(cartilla, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def cartilla_by_client_record(request, client_record_id):
    queryset = _visible_cartillas(request.user)
    user_id = request.query_params.get("user_id")
    if user_id and (request.user.is_staff or request.user.is_superuser):
        queryset = queryset.filter(user_id=user_id)
    cartilla = queryset.filter(client_record_id=client_record_id).first()
    if cartilla is None:
        return Response(
            {"detail": "Cartilla no encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    serializer = CartillaMinaDetailSerializer(cartilla, context={"request": request})
    return Response(serializer.data)
