from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from auth_api.serializers import get_user_roles
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


ACTION_SUBMIT = "submit"
ACTION_OBSERVE = "observe"
ACTION_APPROVE = "approve"
ACTION_REJECT = "reject"
ACTION_CLOSE = "close"


WORKFLOW_ACTIONS = {
    ACTION_SUBMIT: {
        "to_state": CartillaOperacionMina.ESTADO_ENVIADO,
        "from_states": {
            CartillaOperacionMina.ESTADO_BORRADOR,
            CartillaOperacionMina.ESTADO_OBSERVADO,
        },
        "requires_comment": False,
        "permission": "submit",
    },
    ACTION_OBSERVE: {
        "to_state": CartillaOperacionMina.ESTADO_OBSERVADO,
        "from_states": {CartillaOperacionMina.ESTADO_ENVIADO},
        "requires_comment": True,
        "permission": "review",
    },
    ACTION_APPROVE: {
        "to_state": CartillaOperacionMina.ESTADO_APROBADO,
        "from_states": {CartillaOperacionMina.ESTADO_ENVIADO},
        "requires_comment": False,
        "permission": "review",
    },
    ACTION_REJECT: {
        "to_state": CartillaOperacionMina.ESTADO_RECHAZADO,
        "from_states": {
            CartillaOperacionMina.ESTADO_ENVIADO,
            CartillaOperacionMina.ESTADO_OBSERVADO,
        },
        "requires_comment": True,
        "permission": "review",
    },
    ACTION_CLOSE: {
        "to_state": CartillaOperacionMina.ESTADO_CERRADO,
        "from_states": {CartillaOperacionMina.ESTADO_APROBADO},
        "requires_comment": False,
        "permission": "close",
    },
}


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


def _role_codes(user):
    return set(get_user_roles(user))


def _has_any_role(user, role_codes):
    return bool(_role_codes(user) & set(role_codes))


def _can_manage_all(user):
    return user.is_staff or user.is_superuser or _has_any_role(user, ["admin"])


def _can_review(user):
    return _can_manage_all(user) or _has_any_role(user, ["supervisor", "revisor"])


def _can_close(user):
    return _can_review(user)


def _can_see_for_workflow(user, cartilla):
    return cartilla.user_id == user.id or _can_review(user)


def _has_workflow_permission(user, cartilla, permission):
    if permission == "submit":
        return cartilla.user_id == user.id or _can_manage_all(user)
    if permission == "review":
        return _can_review(user)
    if permission == "close":
        return _can_close(user)
    return False


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


def _workflow_cartilla_response(cartilla_id, request):
    cartilla = _base_cartilla_queryset().filter(pk=cartilla_id).first()
    serializer = CartillaMinaListSerializer(cartilla, context={"request": request})
    return Response(serializer.data)


def _workflow_action(request, cartilla_id, action):
    config = WORKFLOW_ACTIONS[action]
    cartilla = CartillaOperacionMina.objects.filter(pk=cartilla_id).first()
    if cartilla is None or not _can_see_for_workflow(request.user, cartilla):
        return Response(
            {"detail": "Cartilla no encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if cartilla.estado_workflow not in config["from_states"]:
        return Response(
            {
                "detail": (
                    f"Transicion invalida: {cartilla.estado_workflow} -> "
                    f"{config['to_state']}."
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not _has_workflow_permission(request.user, cartilla, config["permission"]):
        return Response(
            {"detail": "No tiene permiso para ejecutar esta accion."},
            status=status.HTTP_403_FORBIDDEN,
        )

    comment = (request.data.get("comment") or "").strip()
    if config["requires_comment"] and not comment:
        return Response(
            {"comment": "Este campo es requerido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from_state = cartilla.estado_workflow
    to_state = config["to_state"]
    now = timezone.now()

    with transaction.atomic():
        cartilla.estado_workflow = to_state
        update_fields = ["estado_workflow", "updated_at"]

        if action == ACTION_SUBMIT:
            cartilla.submitted_at = now
            update_fields.append("submitted_at")
        elif action in {ACTION_APPROVE, ACTION_REJECT}:
            cartilla.reviewed_by = request.user
            cartilla.reviewed_at = now
            update_fields.extend(["reviewed_by", "reviewed_at"])
        elif action == ACTION_CLOSE:
            cartilla.closed_at = now
            update_fields.append("closed_at")

        cartilla.save(update_fields=update_fields)
        CartillaWorkflowLog.objects.create(
            cartilla=cartilla,
            from_state=from_state,
            to_state=to_state,
            action=action,
            comment=comment,
            created_by=request.user,
        )

    return _workflow_cartilla_response(cartilla.pk, request)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cartilla_submit(request, cartilla_id):
    return _workflow_action(request, cartilla_id, ACTION_SUBMIT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cartilla_observe(request, cartilla_id):
    return _workflow_action(request, cartilla_id, ACTION_OBSERVE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cartilla_approve(request, cartilla_id):
    return _workflow_action(request, cartilla_id, ACTION_APPROVE)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cartilla_reject(request, cartilla_id):
    return _workflow_action(request, cartilla_id, ACTION_REJECT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cartilla_close(request, cartilla_id):
    return _workflow_action(request, cartilla_id, ACTION_CLOSE)
