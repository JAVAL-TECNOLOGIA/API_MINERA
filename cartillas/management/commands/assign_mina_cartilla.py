from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from cartillas.models import AsignacionCartillaUsuario, TipoCartilla


class Command(BaseCommand):
    help = "Asigna idempotentemente una TipoCartilla Mina a un usuario existente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            required=True,
            help="Username existente al que se asignara la cartilla.",
        )
        parser.add_argument(
            "--cartilla-code",
            default="CARTILLA_OPERACION_MINA",
            help="Codigo de TipoCartilla a asignar.",
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        cartilla_code = options["cartilla_code"].strip()

        if not username:
            raise CommandError("--username no puede estar vacio.")
        if not cartilla_code:
            raise CommandError("--cartilla-code no puede estar vacio.")

        user = self._get_user(username)
        tipo_cartilla = self._get_tipo_cartilla(cartilla_code)
        assignment, created = AsignacionCartillaUsuario.objects.get_or_create(
            user=user,
            tipo_cartilla=tipo_cartilla,
            defaults={
                "estado": AsignacionCartillaUsuario.ESTADO_ACTIVO,
                "deleted_at": None,
            },
        )

        changed = []
        if assignment.estado != AsignacionCartillaUsuario.ESTADO_ACTIVO:
            assignment.estado = AsignacionCartillaUsuario.ESTADO_ACTIVO
            changed.append("estado")
        if assignment.deleted_at is not None:
            assignment.deleted_at = None
            changed.append("deleted_at")

        if changed:
            assignment.updated_at = timezone.now()
            assignment.save(update_fields=changed + ["updated_at"])

        action = "created" if created else "updated" if changed else "unchanged"
        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Asignacion cartilla completada: "
                    f"username={user.username}, "
                    f"cartilla_code={tipo_cartilla.codigo}, "
                    f"estado={assignment.estado}, "
                    f"action={action}"
                ),
            ),
        )

    def _get_user(self, username):
        User = get_user_model()
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"Usuario no existe: {username}") from exc

    def _get_tipo_cartilla(self, cartilla_code):
        try:
            return TipoCartilla.objects.get(
                codigo=cartilla_code,
                is_active=True,
                deleted_at__isnull=True,
            )
        except TipoCartilla.DoesNotExist as exc:
            raise CommandError(
                f"TipoCartilla activa no existe: {cartilla_code}",
            ) from exc
