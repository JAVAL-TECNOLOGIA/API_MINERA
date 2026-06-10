from django.conf import settings
from rest_framework import serializers

from .models import Attachment


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    clientAttachmentId = serializers.CharField(max_length=64)
    moduleKey = serializers.RegexField(
        regex=r"^[A-Za-z0-9_.:-]*$",
        required=False,
        allow_blank=True,
        max_length=100,
    )
    rowKey = serializers.RegexField(
        regex=r"^[A-Za-z0-9_.:-]*$",
        required=False,
        allow_blank=True,
        max_length=64,
    )
    slot = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    attachmentType = serializers.ChoiceField(
        choices=[choice[0] for choice in Attachment.ATTACHMENT_TYPE_CHOICES],
        required=False,
        default=Attachment.TYPE_FOTO,
    )
    originalName = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )
    mimeType = serializers.CharField(required=False, allow_blank=True, max_length=100)

    def validate_file(self, file_obj):
        max_bytes = settings.ATTACHMENT_MAX_UPLOAD_MB * 1024 * 1024
        if file_obj.size > max_bytes:
            raise serializers.ValidationError(
                f"Archivo supera el maximo de {settings.ATTACHMENT_MAX_UPLOAD_MB} MB.",
            )

        filename = file_obj.name.lower()
        allowed_extensions = (".jpg", ".jpeg", ".png", ".webp", ".pdf")
        if "." in filename and not filename.endswith(allowed_extensions):
            raise serializers.ValidationError(
                "Extension no permitida. Use jpg, jpeg, png, webp o pdf.",
            )
        return file_obj


class AttachmentSerializer(serializers.ModelSerializer):
    cartillaId = serializers.IntegerField(source="cartilla_id", read_only=True)
    clientAttachmentId = serializers.CharField(
        source="client_attachment_id",
        read_only=True,
    )
    moduleKey = serializers.CharField(source="module_key", read_only=True)
    rowKey = serializers.CharField(source="row_key", read_only=True)
    attachmentType = serializers.CharField(source="attachment_type", read_only=True)
    originalName = serializers.CharField(source="original_name", read_only=True)
    mimeType = serializers.CharField(source="mime_type", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "cartillaId",
            "clientAttachmentId",
            "moduleKey",
            "rowKey",
            "slot",
            "attachmentType",
            "url",
            "originalName",
            "mimeType",
            "size",
            "updatedAt",
        ]

    def get_url(self, obj):
        if not obj.file:
            return ""
        return obj.file.url


class AttachmentUploadResponseSerializer(AttachmentSerializer):
    created = serializers.BooleanField(read_only=True)

    class Meta(AttachmentSerializer.Meta):
        fields = AttachmentSerializer.Meta.fields + ["created"]


class AttachmentDeleteResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    deleted = serializers.BooleanField()
