from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from core.models import AuditModel


class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="accounts_user_set",
        related_query_name="accounts_user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="accounts_user_set",
        related_query_name="accounts_user",
    )
    dni = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["username"]),
            models.Index(fields=["email"]),
            models.Index(fields=["dni"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["updated_at"]),
        ]

    def __str__(self) -> str:
        return self.get_username()


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
