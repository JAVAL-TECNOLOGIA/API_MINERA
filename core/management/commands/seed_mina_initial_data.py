import json
import os
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Role, UserProfile
from catalogos.models import Area, Clima, Producto, Turno, UnidadMedida
from cartillas.models import TipoCartilla


ROLES = [
    {
        "code": "admin",
        "name": "Administrador",
        "description": "Acceso completo a administracion, configuracion y operacion.",
    },
    {
        "code": "operador",
        "name": "Operador",
        "description": "Registro operativo de cartillas desde campo.",
    },
    {
        "code": "supervisor",
        "name": "Supervisor",
        "description": "Supervision y revision operativa de cartillas.",
    },
    {
        "code": "revisor",
        "name": "Revisor / Aprobador",
        "description": "Revision, observacion y aprobacion de cartillas.",
    },
    {
        "code": "solo_lectura",
        "name": "Solo lectura",
        "description": "Consulta de informacion sin permisos de modificacion.",
    },
]


AREAS = [
    {
        "codigo": "MANT",
        "nombre": "Mantenimiento",
        "descripcion": "Area de mantenimiento.",
    },
    {
        "codigo": "OP_MINA",
        "nombre": "Operaciones Mina",
        "descripcion": "Area de operaciones de mina subterranea.",
    },
]


TURNOS = [
    {
        "codigo": "DIA",
        "nombre": "Dia",
        "hora_inicio": time(7, 0),
        "hora_fin": time(19, 0),
        "cruza_medianoche": False,
    },
    {
        "codigo": "NOCHE",
        "nombre": "Noche",
        "hora_inicio": time(19, 0),
        "hora_fin": time(7, 0),
        "cruza_medianoche": True,
    },
]


PRODUCTOS = [
    {"codigo": "MINERAL", "nombre": "Mineral", "descripcion": "Material mineral."},
    {"codigo": "DESMONTE", "nombre": "Desmonte", "descripcion": "Material desmonte."},
]


UNIDADES_MEDIDA = [
    {"codigo": "M", "nombre": "Metro", "descripcion": "Medida en metros."},
    {"codigo": "KG", "nombre": "Kilogramo", "descripcion": "Medida en kilogramos."},
    {"codigo": "UND", "nombre": "Unidad", "descripcion": "Conteo por unidad."},
]


CLIMAS = [
    {"codigo": "SOLEADO", "nombre": "Soleado", "descripcion": "Clima soleado."},
    {"codigo": "NUBLADO", "nombre": "Nublado", "descripcion": "Clima nublado."},
    {"codigo": "LLUVIA", "nombre": "Lluvia", "descripcion": "Presencia de lluvia."},
    {"codigo": "NEBLINA", "nombre": "Neblina", "descripcion": "Presencia de neblina."},
    {"codigo": "OTRO", "nombre": "Otro", "descripcion": "Otra condicion climatica."},
]


CARTILLA_SCHEMA = {
    "templateKey": "CARTILLA_OPERACION_MINA",
    "version": 1,
    "modules": [
        {"key": "datosGenerales", "title": "Datos generales"},
        {"key": "perforacionVoladura", "title": "Perforacion y voladura"},
        {"key": "extraccionAcarreo", "title": "Extraccion / acarreo"},
        {"key": "personal", "title": "Control de personal"},
        {"key": "equipos", "title": "Control de equipos"},
        {"key": "avances", "title": "Avances en galerias/subniveles"},
        {"key": "observaciones", "title": "Observaciones y acciones correctivas"},
        {"key": "firmas", "title": "Firmas y cierre"},
    ],
}


class Command(BaseCommand):
    help = "Seed inicial idempotente para Cartillas Operaciones Mina."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default=os.getenv("INITIAL_ADMIN_USERNAME", ""))
        parser.add_argument("--admin-password", default=os.getenv("INITIAL_ADMIN_PASSWORD", ""))
        parser.add_argument("--admin-email", default=os.getenv("INITIAL_ADMIN_EMAIL", ""))
        parser.add_argument("--admin-dni", default=os.getenv("INITIAL_ADMIN_DNI", ""))
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra que datos se sembrarian sin escribir en la base.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self._print_dry_run(options)
            return

        with transaction.atomic():
            summary = {
                "roles": self._seed_roles(),
                "areas": self._seed_catalog(Area, AREAS),
                "turnos": self._seed_turnos(),
                "productos": self._seed_catalog(Producto, PRODUCTOS),
                "unidades_medida": self._seed_catalog(UnidadMedida, UNIDADES_MEDIDA),
                "climas": self._seed_catalog(Clima, CLIMAS),
                "tipo_cartilla": self._seed_tipo_cartilla(),
                "admin_user": self._seed_admin_user(options),
            }

        self._print_summary(summary)

    def _seed_roles(self):
        result = {"created": 0, "updated": 0}
        for role in ROLES:
            _, created = Role.objects.update_or_create(
                code=role["code"],
                defaults={
                    "name": role["name"],
                    "description": role["description"],
                    "is_active": True,
                },
            )
            result["created" if created else "updated"] += 1
        return result

    def _seed_catalog(self, model, rows):
        result = {"created": 0, "updated": 0}
        for row in rows:
            _, created = model.objects.update_or_create(
                codigo=row["codigo"],
                defaults={**row, "is_active": True},
            )
            result["created" if created else "updated"] += 1
        return result

    def _seed_turnos(self):
        result = {"created": 0, "updated": 0}
        for row in TURNOS:
            _, created = Turno.objects.update_or_create(
                codigo=row["codigo"],
                defaults={**row, "is_active": True},
            )
            result["created" if created else "updated"] += 1
        return result

    def _seed_tipo_cartilla(self):
        _, created = TipoCartilla.objects.update_or_create(
            codigo="CARTILLA_OPERACION_MINA",
            defaults={
                "nombre": "Cartilla diaria de operacion mina",
                "descripcion": (
                    "Cartilla diaria/por turno para operaciones de mina subterranea"
                ),
                "version": 1,
                "schema_json": json.dumps(CARTILLA_SCHEMA, ensure_ascii=False),
                "is_active": True,
            },
        )
        return {"created": int(created), "updated": int(not created)}

    def _seed_admin_user(self, options):
        username = options["admin_username"].strip()
        password = options["admin_password"]
        email = options["admin_email"].strip()
        dni = options["admin_dni"].strip()

        if not username and not password and not email and not dni:
            return {"skipped": True, "reason": "sin credenciales iniciales"}

        if not username or not password:
            raise CommandError(
                "Para crear admin inicial debe indicar admin username y password."
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "dni": dni or None,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        changed_fields = []
        for field, value in {
            "email": email,
            "dni": dni or None,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        if created:
            user.set_password(password)
            changed_fields.append("password")

        if changed_fields:
            user.save()

        admin_role = Role.objects.get(code="admin")
        profile, profile_created = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "role": admin_role,
                "is_active": True,
            },
        )

        return {
            "skipped": False,
            "created": created,
            "updated": bool(changed_fields) and not created,
            "profile_created": profile_created,
            "profile_id": profile.id,
            "username": user.username,
        }

    def _print_dry_run(self, options):
        self.stdout.write(self.style.WARNING("DRY RUN: no se escribira en la base."))
        self.stdout.write(f"Roles: {len(ROLES)}")
        self.stdout.write(f"Areas: {len(AREAS)}")
        self.stdout.write(f"Turnos: {len(TURNOS)}")
        self.stdout.write(f"Productos: {len(PRODUCTOS)}")
        self.stdout.write(f"Unidades de medida: {len(UNIDADES_MEDIDA)}")
        self.stdout.write(f"Climas: {len(CLIMAS)}")
        self.stdout.write("TipoCartilla: CARTILLA_OPERACION_MINA")
        if options["admin_username"] or options["admin_password"]:
            self.stdout.write(f"Admin inicial: {options['admin_username'] or '(sin usuario)'}")
        else:
            self.stdout.write("Admin inicial: omitido")

    def _print_summary(self, summary):
        self.stdout.write(self.style.SUCCESS("Seed Mina Carolina completado."))
        for key, value in summary.items():
            self.stdout.write(f"{key}: {value}")
