from django.utils.dateparse import parse_datetime
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .models import AsignacionCartillaUsuario, TipoCartilla
from .serializers import TipoCartillaSerializer


def tipos_cartilla_for_user(user, updated_since=None):
    assigned_ids = AsignacionCartillaUsuario.objects.filter(
        user=user,
        estado=AsignacionCartillaUsuario.ESTADO_ACTIVO,
        deleted_at__isnull=True,
        tipo_cartilla__is_active=True,
        tipo_cartilla__deleted_at__isnull=True,
    ).values_list("tipo_cartilla_id", flat=True)

    assigned_ids = list(assigned_ids)
    if assigned_ids:
        queryset = TipoCartilla.objects.filter(id__in=assigned_ids)
    else:
        queryset = TipoCartilla.objects.filter(is_active=True, deleted_at__isnull=True)

    if updated_since:
        parsed = (
            parse_datetime(updated_since)
            if isinstance(updated_since, str)
            else updated_since
        )
        if parsed:
            queryset = queryset.filter(updated_at__gte=parsed)

    return queryset.order_by("codigo", "version")


class TipoCartillaListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TipoCartillaSerializer

    def get_queryset(self):
        return tipos_cartilla_for_user(
            self.request.user,
            updated_since=self.request.query_params.get("updated_since"),
        )
