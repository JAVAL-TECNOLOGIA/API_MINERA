from django.conf import settings
from django.db import models

from core.models import AuditModel


class Role(AuditModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class UserProfile(AuditModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mina_profiles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_profiles",
    )
    empresa = models.ForeignKey(
        "catalogos.Empresa",
        on_delete=models.PROTECT,
        related_name="user_profiles",
        blank=True,
        null=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.role}"

# Create your models here.
