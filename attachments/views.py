from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from auth_api.serializers import get_user_roles
from mina.models import CartillaOperacionMina

from .models import Attachment
from .serializers import (
    AttachmentDeleteResponseSerializer,
    AttachmentSerializer,
    AttachmentUploadResponseSerializer,
    AttachmentUploadSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def module_status(request):
    return Response({"module": "attachments", "status": "ready"})


def _can_access_cartilla(user, cartilla):
    if cartilla.user_id == user.id or user.is_superuser:
        return True
    return bool({"admin", "supervisor", "revisor"} & set(get_user_roles(user)))


def _get_cartilla_or_response(request, cartilla_id):
    cartilla = CartillaOperacionMina.objects.filter(pk=cartilla_id).first()
    if cartilla is None:
        return None, Response(
            {"detail": "Cartilla no encontrada."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if not _can_access_cartilla(request.user, cartilla):
        return None, Response(
            {"detail": "No tiene permiso para esta cartilla."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return cartilla, None


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def cartilla_attachments(request, cartilla_id):
    cartilla, error_response = _get_cartilla_or_response(request, cartilla_id)
    if error_response:
        return error_response

    if request.method == "GET":
        attachments = cartilla.attachments.filter(deleted_at__isnull=True).order_by(
            "module_key",
            "row_key",
            "slot",
            "id",
        )
        serializer = AttachmentSerializer(
            attachments,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    serializer = AttachmentUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    file_obj = data["file"]

    attachment, created = Attachment.objects.get_or_create(
        cartilla=cartilla,
        client_attachment_id=data["clientAttachmentId"],
        defaults={"created_by": request.user},
    )

    old_file_name = attachment.file.name if attachment.pk and attachment.file else ""
    old_file_storage = attachment.file.storage if old_file_name else None
    attachment.module_key = data.get("moduleKey", "") or ""
    attachment.row_key = data.get("rowKey", "") or ""
    attachment.slot = data.get("slot")
    attachment.attachment_type = data.get("attachmentType") or Attachment.TYPE_FOTO
    attachment.original_name = data.get("originalName") or file_obj.name
    attachment.mime_type = data.get("mimeType") or getattr(file_obj, "content_type", "") or ""
    attachment.size = file_obj.size
    if not attachment.created_by_id:
        attachment.created_by = request.user
    attachment.deleted_at = None
    attachment.file = file_obj
    attachment.save()

    if old_file_name and old_file_name != attachment.file.name:
        old_file_storage.delete(old_file_name)

    response = AttachmentUploadResponseSerializer(
        attachment,
        context={"request": request},
    ).data
    response["created"] = created
    return Response(
        response,
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_attachment(request, attachment_id):
    attachment = Attachment.objects.select_related("cartilla").filter(
        pk=attachment_id,
    ).first()
    if attachment is None or attachment.deleted_at is not None:
        return Response(
            {"detail": "Attachment no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
    if not _can_access_cartilla(request.user, attachment.cartilla):
        return Response(
            {"detail": "No tiene permiso para este attachment."},
            status=status.HTTP_403_FORBIDDEN,
        )

    attachment.deleted_at = timezone.now()
    attachment.save(update_fields=["deleted_at", "updated_at"])
    serializer = AttachmentDeleteResponseSerializer(
        {"id": attachment.pk, "deleted": True},
    )
    return Response(serializer.data)
