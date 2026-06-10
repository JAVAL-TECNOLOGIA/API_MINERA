from django.conf import settings
from django.db import models

from core.models import SoftDeleteModel, TimeStampedModel


class Attachment(TimeStampedModel, SoftDeleteModel):
    TYPE_FOTO = "foto"
    TYPE_FIRMA = "firma"
    TYPE_DOCUMENTO = "documento"
    TYPE_EVIDENCIA = "evidencia"

    ATTACHMENT_TYPE_CHOICES = [
        (TYPE_FOTO, "Foto"),
        (TYPE_FIRMA, "Firma"),
        (TYPE_DOCUMENTO, "Documento"),
        (TYPE_EVIDENCIA, "Evidencia"),
    ]

    cartilla = models.ForeignKey(
        "mina.CartillaOperacionMina",
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    client_attachment_id = models.CharField(max_length=64)
    module_key = models.CharField(max_length=100)
    row_key = models.CharField(max_length=64, blank=True)
    slot = models.PositiveIntegerField(blank=True, null=True)
    attachment_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        default=TYPE_FOTO,
    )
    file = models.FileField(upload_to="attachments/%Y/%m/%d/")
    original_name = models.CharField(max_length=255, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveBigIntegerField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mina_attachments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cartilla", "client_attachment_id"],
                name="uq_attachment_cartilla_client_id",
            ),
        ]
        indexes = [
            models.Index(fields=["module_key"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return self.original_name or self.client_attachment_id

# Create your models here.
