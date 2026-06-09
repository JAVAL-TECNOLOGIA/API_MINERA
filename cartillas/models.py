from django.conf import settings
from django.db import models

from core.models import AuditModel, SoftDeleteModel


class TipoCartilla(AuditModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    schema_json = models.TextField(default="{}", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} v{self.version} - {self.nombre}"


class AsignacionCartillaUsuario(SoftDeleteModel):
    ESTADO_ACTIVO = "activo"
    ESTADO_INACTIVO = "inactivo"

    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_INACTIVO, "Inactivo"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asignaciones_cartilla_mina",
    )
    tipo_cartilla = models.ForeignKey(
        TipoCartilla,
        on_delete=models.PROTECT,
        related_name="asignaciones_usuario",
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_ACTIVO,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tipo_cartilla"],
                name="uq_asignacion_cartilla_usuario",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.tipo_cartilla} ({self.estado})"

# Create your models here.
