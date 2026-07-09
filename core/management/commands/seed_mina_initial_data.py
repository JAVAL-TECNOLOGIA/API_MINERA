import json
import os
from datetime import time

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


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


GUARDIAS = [
    {"codigo": "A", "nombre": "Guardia A", "descripcion": "Guardia operativa A."},
    {"codigo": "B", "nombre": "Guardia B", "descripcion": "Guardia operativa B."},
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
    {"codigo": "L", "nombre": "Litro", "descripcion": "Medida en litros."},
]

SUCURSALES = [
    {
        "codigo": "MINA_CAROLINA_JE",
        "nombre": "Mina Carolina JE.",
        "descripcion": "Sucursal Mina Carolina JE.",
    },
]

REQUERIMIENTO_RUBROS = [
    {"codigo": "HERRAMIENTA", "nombre": "Herramienta", "descripcion": "Herramientas."},
    {"codigo": "ACCESORIO", "nombre": "Accesorio", "descripcion": "Accesorios."},
    {"codigo": "REPUESTO", "nombre": "Repuesto", "descripcion": "Repuestos."},
    {"codigo": "EPP", "nombre": "EPP", "descripcion": "Equipo de proteccion personal."},
]

REQUERIMIENTO_PRODUCTOS = [
    ("COMBA_4_LB", "Comba de 4 lbs.", "herramientas_otros", "HERRAMIENTA", "UND"),
    ("CHALONA", "Chalona", "herramientas_otros", "ACCESORIO", "UND"),
    ("ACEITE", "Aceite", "herramientas_otros", "REPUESTO", "L"),
    ("PANTALON_PERFORAR", "Pantalon para perforar", "equipo_proteccion_personal", "EPP", "UND"),
    ("BUZO_REFLECTIVO", "Buzo con cinta reflectiva", "equipo_proteccion_personal", "EPP", "UND"),
    ("POLO_REFLECTIVO", "Polo manga larga con cinta reflectiva", "equipo_proteccion_personal", "EPP", "UND"),
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

CARTILLA_TYPES = [
    (
        "CARTILLA_OPERACION_MINA",
        "Cartilla diaria de operacion mina",
        "Cartilla diaria/por turno para operaciones de mina subterranea",
        CARTILLA_SCHEMA,
    ),
    (
        "CARTILLA_REQUERIMIENTO_PRODUCTOS",
        "Cartilla de requerimiento de productos",
        "Solicitud de herramientas, accesorios, repuestos y EPP por sucursal.",
        {
            "sections": [
                "datosGenerales",
                "herramientasOtros",
                "equipoProteccionPersonal",
            ],
        },
    ),
]


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

        summary = {
            "roles": self._seed_roles(),
            "areas": self._seed_catalog("catalogos_area", AREAS),
            "guardias": self._seed_catalog("catalogos_guardia", GUARDIAS),
            "turnos": self._seed_turnos(),
            "productos": self._seed_catalog("catalogos_producto", PRODUCTOS),
            "unidades_medida": self._seed_catalog(
                "catalogos_unidadmedida",
                UNIDADES_MEDIDA,
            ),
            "sucursales": self._seed_catalog("catalogos_sucursal", SUCURSALES),
            "requerimiento_rubros": self._seed_catalog(
                "catalogos_requerimientorubro",
                REQUERIMIENTO_RUBROS,
            ),
            "requerimiento_productos": self._seed_requerimiento_productos(),
            "climas": self._seed_catalog("catalogos_clima", CLIMAS),
            "tipos_cartilla": self._seed_tipo_cartilla(),
            "admin_user": self._seed_admin_user(options),
        }

        self._print_summary(summary)

    def _seed_roles(self):
        result = {"created": 0, "updated": 0}
        for role in ROLES:
            existed = self._exists("accounts_role", "code", role["code"])
            self._execute(
                f"""
                IF EXISTS (SELECT 1 FROM accounts_role WHERE code = {self._q(role["code"])})
                    UPDATE accounts_role
                    SET name = {self._q(role["name"])},
                        description = {self._q(role["description"])},
                        is_active = 1,
                        updated_at = GETDATE()
                    WHERE code = {self._q(role["code"])}
                ELSE
                    INSERT INTO accounts_role
                        (created_at, updated_at, deleted_at, is_active, code, name, description)
                    VALUES
                        (GETDATE(), GETDATE(), NULL, 1, {self._q(role["code"])},
                         {self._q(role["name"])}, {self._q(role["description"])})
                """
            )
            result["updated" if existed else "created"] += 1
        return result

    def _seed_catalog(self, table_name, rows):
        result = {"created": 0, "updated": 0}
        for row in rows:
            existed = self._exists(table_name, "codigo", row["codigo"])
            self._execute(
                f"""
                IF EXISTS (SELECT 1 FROM {table_name} WHERE codigo = {self._q(row["codigo"])})
                    UPDATE {table_name}
                    SET nombre = {self._q(row["nombre"])},
                        descripcion = {self._q(row["descripcion"])},
                        is_active = 1,
                        updated_at = GETDATE()
                    WHERE codigo = {self._q(row["codigo"])}
                ELSE
                    INSERT INTO {table_name}
                        (created_at, updated_at, deleted_at, is_active, codigo, nombre, descripcion)
                    VALUES
                        (GETDATE(), GETDATE(), NULL, 1, {self._q(row["codigo"])},
                         {self._q(row["nombre"])}, {self._q(row["descripcion"])})
                """
            )
            result["updated" if existed else "created"] += 1
        return result

    def _seed_turnos(self):
        result = {"created": 0, "updated": 0}
        for row in TURNOS:
            existed = self._exists("catalogos_turno", "codigo", row["codigo"])
            self._execute(
                f"""
                IF EXISTS (SELECT 1 FROM catalogos_turno WHERE codigo = {self._q(row["codigo"])})
                    UPDATE catalogos_turno
                    SET nombre = {self._q(row["nombre"])},
                        hora_inicio = {self._time(row["hora_inicio"])},
                        hora_fin = {self._time(row["hora_fin"])},
                        cruza_medianoche = {self._bit(row["cruza_medianoche"])},
                        is_active = 1,
                        updated_at = GETDATE()
                    WHERE codigo = {self._q(row["codigo"])}
                ELSE
                    INSERT INTO catalogos_turno
                        (created_at, updated_at, deleted_at, is_active, codigo, nombre,
                         hora_inicio, hora_fin, cruza_medianoche)
                    VALUES
                        (GETDATE(), GETDATE(), NULL, 1, {self._q(row["codigo"])},
                         {self._q(row["nombre"])}, {self._time(row["hora_inicio"])},
                         {self._time(row["hora_fin"])}, {self._bit(row["cruza_medianoche"])})
                """
            )
            result["updated" if existed else "created"] += 1
        return result

    def _seed_requerimiento_productos(self):
        result = {"created": 0, "updated": 0}
        for codigo, nombre, seccion, rubro_codigo, unidad_codigo in REQUERIMIENTO_PRODUCTOS:
            existed = self._exists("catalogos_requerimientoproducto", "codigo", codigo)
            self._execute(
                f"""
                DECLARE @rubro_id bigint =
                    (SELECT TOP 1 id FROM catalogos_requerimientorubro
                     WHERE codigo = {self._q(rubro_codigo)});
                DECLARE @unidad_id bigint =
                    (SELECT TOP 1 id FROM catalogos_unidadmedida
                     WHERE codigo = {self._q(unidad_codigo)});

                IF EXISTS (
                    SELECT 1 FROM catalogos_requerimientoproducto
                    WHERE codigo = {self._q(codigo)}
                )
                    UPDATE catalogos_requerimientoproducto
                    SET nombre = {self._q(nombre)},
                        descripcion = {self._q(nombre)},
                        seccion = {self._q(seccion)},
                        rubro_id = @rubro_id,
                        unidad_medida_id = @unidad_id,
                        is_active = 1,
                        updated_at = GETDATE()
                    WHERE codigo = {self._q(codigo)}
                ELSE
                    INSERT INTO catalogos_requerimientoproducto
                        (created_at, updated_at, deleted_at, is_active, codigo,
                         nombre, descripcion, seccion, rubro_id, unidad_medida_id)
                    VALUES
                        (GETDATE(), GETDATE(), NULL, 1, {self._q(codigo)},
                         {self._q(nombre)}, {self._q(nombre)}, {self._q(seccion)},
                         @rubro_id, @unidad_id)
                """
            )
            result["updated" if existed else "created"] += 1
        return result

    def _seed_tipo_cartilla(self):
        result = {"created": 0, "updated": 0}
        for codigo, nombre, descripcion, schema in CARTILLA_TYPES:
            schema_json = json.dumps(schema, ensure_ascii=False)
            existed = self._exists("cartillas_tipocartilla", "codigo", codigo)
            self._execute(
                f"""
                IF EXISTS (SELECT 1 FROM cartillas_tipocartilla WHERE codigo = {self._q(codigo)})
                    UPDATE cartillas_tipocartilla
                    SET nombre = {self._q(nombre)},
                        descripcion = {self._q(descripcion)},
                        version = 1,
                        schema_json = {self._q(schema_json)},
                        is_active = 1,
                        updated_at = GETDATE()
                    WHERE codigo = {self._q(codigo)}
                ELSE
                    INSERT INTO cartillas_tipocartilla
                        (created_at, updated_at, deleted_at, is_active, codigo,
                         nombre, descripcion, version, schema_json)
                    VALUES
                        (GETDATE(), GETDATE(), NULL, 1, {self._q(codigo)},
                         {self._q(nombre)}, {self._q(descripcion)}, 1, {self._q(schema_json)})
                """
            )
            result["updated" if existed else "created"] += 1
        return result

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

        existed = self._exists("accounts_user", "username", username)
        password_hash = make_password(password)
        dni_sql = self._q(dni) if dni else "NULL"

        self._execute(
            f"""
            IF EXISTS (SELECT 1 FROM accounts_user WHERE username = {self._q(username)})
                UPDATE accounts_user
                SET email = {self._q(email)},
                    dni = {dni_sql},
                    is_staff = 1,
                    is_superuser = 1,
                    is_active = 1,
                    updated_at = GETDATE()
                WHERE username = {self._q(username)}
            ELSE
                INSERT INTO accounts_user
                    (password, last_login, is_superuser, username, first_name, last_name,
                     email, is_staff, is_active, date_joined, dni, phone,
                     created_at, updated_at, deleted_at)
                VALUES
                    ({self._q(password_hash)}, NULL, 1, {self._q(username)}, '', '',
                     {self._q(email)}, 1, 1, GETDATE(), {dni_sql}, '',
                     GETDATE(), GETDATE(), NULL)
            """
        )

        profile_existed = self._admin_profile_exists(username)
        self._execute(
            f"""
            DECLARE @user_id bigint = (
                SELECT TOP 1 id FROM accounts_user WHERE username = {self._q(username)}
            );
            DECLARE @role_id bigint = (
                SELECT TOP 1 id FROM accounts_role WHERE code = 'admin'
            );

            IF EXISTS (SELECT 1 FROM accounts_userprofile WHERE user_id = @user_id)
                UPDATE accounts_userprofile
                SET role_id = @role_id,
                    is_active = 1,
                    updated_at = GETDATE()
                WHERE user_id = @user_id
            ELSE
                INSERT INTO accounts_userprofile
                    (created_at, updated_at, deleted_at, is_active,
                     user_id, role_id, empresa_id)
                VALUES
                    (GETDATE(), GETDATE(), NULL, 1, @user_id, @role_id, NULL)
            """
        )

        return {
            "skipped": False,
            "created": not existed,
            "updated": existed,
            "profile_created": not profile_existed,
            "username": username,
        }

    def _exists(self, table_name, field_name, value):
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE {field_name} = {self._q(value)}"
            )
            return cursor.fetchone()[0] > 0

    def _admin_profile_exists(self, username):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM accounts_userprofile p
                INNER JOIN accounts_user u ON u.id = p.user_id
                WHERE u.username = {self._q(username)}
                """
            )
            return cursor.fetchone()[0] > 0

    def _execute(self, sql):
        with connection.cursor() as cursor:
            cursor.execute(sql)

    def _q(self, value):
        return "N'" + str(value).replace("'", "''") + "'"

    def _time(self, value):
        return "'" + value.strftime("%H:%M:%S") + "'"

    def _bit(self, value):
        return "1" if value else "0"

    def _print_dry_run(self, options):
        self.stdout.write(self.style.WARNING("DRY RUN: no se escribira en la base."))
        self.stdout.write(f"Roles: {len(ROLES)}")
        self.stdout.write(f"Areas: {len(AREAS)}")
        self.stdout.write(f"Guardias: {len(GUARDIAS)}")
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
