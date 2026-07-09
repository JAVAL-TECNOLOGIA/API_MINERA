import json
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Role, UserProfile
from cartillas.models import AsignacionCartillaUsuario, TipoCartilla
from cartillas.views import tipos_cartilla_for_user
from catalogos.models import (
    Area,
    Cargo,
    Clima,
    Empresa,
    Equipo,
    Explosivo,
    GrupoPerforacion,
    GrupoPerforacionIntegrante,
    Guardia,
    InsumoAccesorio,
    Labor,
    LaborFrente,
    Nivel,
    Producto,
    RequerimientoProducto,
    RequerimientoRubro,
    Sucursal,
    Trabajador,
    Turno,
    UnidadMedida,
    Zona,
)
from sync.views import catalog_payload


CARTILLA_CODE = "CARTILLA_OPERACION_MINA"
REQUERIMIENTO_CARTILLA_CODE = "CARTILLA_REQUERIMIENTO_PRODUCTOS"

ROLES = [
    ("admin", "Administrador", "Acceso completo a administracion y operacion."),
    ("operador", "Operador", "Registro operativo de cartillas desde campo."),
    ("supervisor", "Supervisor", "Supervision y revision operativa."),
    ("revisor", "Revisor / Aprobador", "Revision y aprobacion de cartillas."),
    ("solo_lectura", "Solo lectura", "Consulta de informacion."),
]

CATALOG_BASE = {
    Area: [
        ("OP_MINA", "Operaciones Mina", "Area demo para operacion mina."),
        ("MANT", "Mantenimiento", "Area demo para mantenimiento."),
    ],
    Guardia: [
        ("G1", "Guardia 1", "Guardia demo 1."),
        ("G2", "Guardia 2", "Guardia demo 2."),
        ("G3", "Guardia 3", "Guardia demo 3."),
        ("G4", "Guardia 4", "Guardia demo 4."),
    ],
    Clima: [
        ("SOLEADO", "Soleado", "Clima soleado."),
        ("NUBLADO", "Nublado", "Clima nublado."),
        ("LLUVIA", "Lluvia", "Presencia de lluvia."),
        ("NEBLINA", "Neblina", "Presencia de neblina."),
        ("OTRO", "Otro", "Otra condicion climatica."),
    ],
    Producto: [
        ("MINERAL", "Mineral", "Material mineral."),
        ("DESMONTE", "Desmonte", "Material desmonte."),
    ],
    UnidadMedida: [
        ("M", "Metro", "Medida en metros."),
        ("KG", "Kilogramo", "Medida en kilogramos."),
        ("UND", "Unidad", "Conteo por unidad."),
        ("CAJA", "Caja", "Conteo por caja."),
        ("SACO", "Saco", "Conteo por saco."),
        ("L", "Litro", "Medida en litros."),
    ],
    Sucursal: [
        ("MINA_CAROLINA_JE", "Mina Carolina JE.", "Sucursal Mina Carolina JE."),
    ],
    RequerimientoRubro: [
        ("HERRAMIENTA", "Herramienta", "Herramientas."),
        ("ACCESORIO", "Accesorio", "Accesorios."),
        ("REPUESTO", "Repuesto", "Repuestos."),
        ("EPP", "EPP", "Equipo de proteccion personal."),
    ],
    Cargo: [
        ("ING_MINERO", "Ingeniero Minero", "Cargo demo Mina."),
        ("SUPERVISOR", "Supervisor", "Cargo demo Mina."),
        ("OPERADOR", "Operador", "Cargo demo Mina."),
        ("PERFORISTA", "Perforista", "Cargo demo Mina."),
        ("AYUDANTE", "Ayudante", "Cargo demo Mina."),
        ("MECANICO", "Mecanico", "Cargo demo Mina."),
        ("ELECTRICISTA", "Electricista", "Cargo demo Mina."),
        ("CAPATAZ", "Capataz", "Cargo demo Mina."),
        ("CONDUCTOR", "Conductor", "Cargo demo Mina."),
        ("SEGURIDAD", "Seguridad", "Cargo demo Mina."),
    ],
}

REQUERIMIENTO_PRODUCTOS = [
    ("COMBA_4_LB", "Comba de 4 lbs.", "herramientas_otros", "HERRAMIENTA", "UND"),
    ("CHALONA", "Chalona", "herramientas_otros", "ACCESORIO", "UND"),
    ("ACEITE", "Aceite", "herramientas_otros", "REPUESTO", "L"),
    ("PANTALON_PERFORAR", "Pantalon para perforar", "equipo_proteccion_personal", "EPP", "UND"),
    ("BUZO_REFLECTIVO", "Buzo con cinta reflectiva", "equipo_proteccion_personal", "EPP", "UND"),
    ("POLO_REFLECTIVO", "Polo manga larga con cinta reflectiva", "equipo_proteccion_personal", "EPP", "UND"),
]

TURNOS = [
    ("DIA", "Dia", time(7, 0), time(19, 0), False),
    ("NOCHE", "Noche", time(19, 0), time(7, 0), True),
]

EMPRESAS = [
    ("EXPLORAMIN", "Exploramin", "Empresa demo principal."),
    ("CONTRATA_MINA", "Contrata Mina", "Contrata demo Mina."),
    ("MANTENIMIENTO", "Servicios de Mantenimiento", "Empresa demo de mantenimiento."),
]

ZONAS = [
    ("ZA", "A", "Zona A", "Zona demo A."),
    ("ZB", "B", "Zona B", "Zona demo B."),
    ("ZC", "C", "Zona C", "Zona demo C."),
]

NIVELES = [
    ("NV100", 100, "Nivel 100"),
    ("NV200", 200, "Nivel 200"),
    ("NV300", 300, "Nivel 300"),
    ("NV400", 400, "Nivel 400"),
]

LABORES = [
    ("LAB-001", "Galeria Principal Norte", "ZA", "NV100"),
    ("LAB-002", "Galeria Principal Sur", "ZB", "NV100"),
    ("LAB-003", "Crucero Este", "ZA", "NV200"),
    ("LAB-004", "Crucero Oeste", "ZB", "NV200"),
    ("LAB-005", "ByPass Central", "ZC", "NV300"),
    ("LAB-006", "Chimenea Ventilacion", "ZC", "NV300"),
    ("LAB-007", "Rampa Acceso", "ZA", "NV400"),
    ("LAB-008", "Subnivel Explotacion", "ZB", "NV400"),
]

FRENTES = [
    ("FRENTE-001", "Frente Galeria Norte 01", "LAB-001"),
    ("FRENTE-002", "Frente Galeria Norte 02", "LAB-001"),
    ("FRENTE-003", "Frente Galeria Sur 01", "LAB-002"),
    ("FRENTE-004", "Frente Galeria Sur 02", "LAB-002"),
    ("FRENTE-005", "Frente Crucero Este 01", "LAB-003"),
    ("FRENTE-006", "Frente Crucero Este 02", "LAB-003"),
    ("FRENTE-007", "Frente Crucero Oeste 01", "LAB-004"),
    ("FRENTE-008", "Frente Crucero Oeste 02", "LAB-004"),
    ("FRENTE-009", "Frente ByPass Central 01", "LAB-005"),
    ("FRENTE-010", "Frente ByPass Central 02", "LAB-005"),
    ("FRENTE-011", "Frente Chimenea Ventilacion 01", "LAB-006"),
    ("FRENTE-012", "Frente Rampa 01", "LAB-007"),
    ("FRENTE-013", "Frente Rampa 02", "LAB-007"),
    ("FRENTE-014", "Frente Subnivel 01", "LAB-008"),
    ("FRENTE-015", "Frente Subnivel 02", "LAB-008"),
]

GRUPOS = [
    ("GP-01", "Grupo Perforacion 1"),
    ("GP-02", "Grupo Perforacion 2"),
    ("GP-03", "Grupo Perforacion 3"),
    ("GP-04", "Grupo Perforacion 4"),
]

EXPLOSIVOS = [
    ("DINAMITA", "Dinamita", "UND"),
    ("EMULSION", "Emulsion", "KG"),
    ("ANFO", "ANFO", "KG"),
    ("FANEL", "Fanel", "UND"),
    ("CORDON_DETONANTE", "Cordon detonante", "M"),
]

INSUMOS = [
    ("NITRATO", "Nitrato", "KG"),
    ("GUIA_SEGURIDAD", "Guia de seguridad", "M"),
    ("MECHA_RAPIDA", "Mecha rapida", "M"),
    ("CARMEX", "Carmex", "UND"),
    ("BROCA", "Broca", "UND"),
    ("BARRENO", "Barreno", "UND"),
    ("MANGUERA_AIRE", "Manguera de aire", "M"),
    ("ACEITE_PERFORADORA", "Aceite perforadora", "L"),
]

EQUIPOS = [
    ("SCOOP-01", "Scoop 01", "Scoop", "EXPLORAMIN"),
    ("SCOOP-02", "Scoop 02", "Scoop", "EXPLORAMIN"),
    ("JUMBO-01", "Jumbo 01", "Jumbo", "CONTRATA_MINA"),
    ("JUMBO-02", "Jumbo 02", "Jumbo", "CONTRATA_MINA"),
    ("DUMPER-01", "Dumper 01", "Dumper", "CONTRATA_MINA"),
    ("DUMPER-02", "Dumper 02", "Dumper", "CONTRATA_MINA"),
    ("CAMION-01", "Camion 01", "Camion", "EXPLORAMIN"),
    ("CAMION-02", "Camion 02", "Camion", "EXPLORAMIN"),
    ("COMPRESORA-01", "Compresora 01", "Compresora", "MANTENIMIENTO"),
    ("PERFORADORA-01", "Perforadora 01", "Perforadora", "MANTENIMIENTO"),
    ("GENERADOR-01", "Generador 01", "Generador", "MANTENIMIENTO"),
    ("CAMIONETA-01", "Camioneta 01", "Camioneta", "EXPLORAMIN"),
]

CARTILLA_SCHEMA = {
    "templateKey": CARTILLA_CODE,
    "version": 1,
    "modules": [
        {"key": "datosGenerales", "title": "Datos generales"},
        {"key": "perforacionVoladura", "title": "Perforacion y voladura"},
        {"key": "extraccionAcarreo", "title": "Extraccion / acarreo"},
        {"key": "personal", "title": "Control de personal"},
        {"key": "equipos", "title": "Control de equipos"},
        {"key": "avances", "title": "Avances"},
        {"key": "observaciones", "title": "Observaciones"},
        {"key": "firmas", "title": "Firmas"},
    ],
}


class Command(BaseCommand):
    help = "Seed demo idempotente para pruebas integrales de Mina Carolina."

    def add_arguments(self, parser):
        parser.add_argument("--with-user", action="store_true")
        parser.add_argument("--username", default="")
        parser.add_argument("--password", default="")
        parser.add_argument("--email", default="")
        parser.add_argument("--dni", default="")
        parser.add_argument(
            "--role",
            default="operador",
            choices=["admin", "operador", "supervisor", "revisor", "solo_lectura"],
        )
        parser.add_argument("--assign-cartilla", action="store_true")
        parser.add_argument(
            "--reset-demo",
            action="store_true",
            help="Reinicia solo relaciones demo seguras antes de resembrar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra datos que se sembrarian sin escribir en la base.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self._print_dry_run(options)
            return

        with transaction.atomic():
            if options["reset_demo"]:
                self._reset_demo_relations()

            summary = {
                "roles": self._seed_roles(),
                "areas": self._seed_catalog_base(Area),
                "guardias": self._seed_catalog_base(Guardia),
                "turnos": self._seed_turnos(),
                "climas": self._seed_catalog_base(Clima),
                "productos": self._seed_catalog_base(Producto),
                "unidades_medida": self._seed_catalog_base(UnidadMedida),
                "sucursales": self._seed_catalog_base(Sucursal),
                "requerimiento_rubros": self._seed_catalog_base(RequerimientoRubro),
                "requerimiento_productos": self._seed_requerimiento_productos(),
                "empresas": self._seed_empresas(),
                "cargos": self._seed_catalog_base(Cargo),
                "trabajadores": self._seed_trabajadores(),
                "zonas": self._seed_zonas(),
                "niveles": self._seed_niveles(),
                "labores": self._seed_labores(),
                "frentes": self._seed_frentes(),
                "grupos_perforacion": self._seed_grupos(),
                "integrantes_grupo": self._seed_integrantes(),
                "explosivos": self._seed_explosivos(),
                "insumos": self._seed_insumos(),
                "equipos": self._seed_equipos(),
                "tipo_cartilla": self._seed_tipo_cartilla(),
            }
            user = self._seed_user(options)
            assignment = self._assign_cartilla_if_requested(user, options)

        counts = self._counts()
        bootstrap = self._validate_bootstrap(user)

        self._print_summary(summary, user, assignment, counts, bootstrap, options)

    def _seed_roles(self):
        result = Counter()
        for code, name, description in ROLES:
            _, created = Role.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_catalog_base(self, model):
        result = Counter()
        for codigo, nombre, descripcion in CATALOG_BASE[model]:
            _, created = model.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_turnos(self):
        result = Counter()
        for codigo, nombre, inicio, fin, cruza in TURNOS:
            _, created = Turno.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "hora_inicio": inicio,
                    "hora_fin": fin,
                    "cruza_medianoche": cruza,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_empresas(self):
        result = Counter()
        for codigo, razon_social, descripcion in EMPRESAS:
            _, created = Empresa.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "ruc": "",
                    "razon_social": razon_social,
                    "descripcion": descripcion,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_trabajadores(self):
        empresas = {
            empresa.codigo: empresa
            for empresa in Empresa.objects.filter(codigo__in=[row[0] for row in EMPRESAS])
        }
        cargos = {
            cargo.codigo: cargo
            for cargo in Cargo.objects.filter(
                codigo__in=[row[0] for row in CATALOG_BASE[Cargo]]
            )
        }
        rows = self._trabajadores_rows()
        result = Counter()

        for row in rows:
            defaults = {
                "dni": row["dni"],
                "nombres": row["nombres"],
                "apellidos": "Demo Mina",
                "cargo": cargos[row["cargo"]],
                "empresa": empresas[row["empresa"]],
                "telefono": "",
                "email": "",
                "es_ingeniero_minero": row.get("ingeniero", False),
                "es_supervisor": row.get("supervisor", False),
                "es_operador": row.get("operador", False),
                "is_active": True,
                "deleted_at": None,
            }
            _, created = update_or_create_by_codigo(Trabajador, row["codigo"], defaults)
            result.add(created)
        return result.as_dict()

    def _trabajadores_rows(self):
        rows = []

        def add(nombres, cargo, empresa, **flags):
            number = len(rows) + 1
            rows.append(
                {
                    "codigo": f"TRAB{number:03d}",
                    "dni": f"900000{number:02d}",
                    "nombres": nombres,
                    "cargo": cargo,
                    "empresa": empresa,
                    **flags,
                }
            )

        for index in range(1, 4):
            add(
                f"Ingeniero Mina {index:02d}",
                "ING_MINERO",
                "EXPLORAMIN",
                ingeniero=True,
            )
        for index in range(1, 6):
            add(
                f"Supervisor Mina {index:02d}",
                "SUPERVISOR",
                "EXPLORAMIN",
                supervisor=True,
            )
        for index in range(1, 11):
            add(
                f"Operador Scoop {index:02d}",
                "OPERADOR",
                "CONTRATA_MINA",
                operador=True,
            )
        for index in range(1, 9):
            add(f"Perforista {index:02d}", "PERFORISTA", "CONTRATA_MINA")
        for index in range(1, 6):
            add(f"Ayudante Mina {index:02d}", "AYUDANTE", "CONTRATA_MINA")
        for index in range(1, 3):
            add(f"Mecanico Mina {index:02d}", "MECANICO", "MANTENIMIENTO")
        for index in range(1, 3):
            add(f"Electricista Mina {index:02d}", "ELECTRICISTA", "MANTENIMIENTO")
        return rows

    def _seed_zonas(self):
        result = Counter()
        for codigo, letra, nombre, descripcion in ZONAS:
            _, created = Zona.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "letra": letra,
                    "nombre": nombre,
                    "descripcion": descripcion,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_niveles(self):
        result = Counter()
        for codigo, numero, descripcion in NIVELES:
            _, created = Nivel.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "numero": numero,
                    "descripcion": descripcion,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_labores(self):
        zonas = {
            zona.codigo: zona
            for zona in Zona.objects.filter(codigo__in=[z[0] for z in ZONAS])
        }
        niveles = {
            nivel.codigo: nivel
            for nivel in Nivel.objects.filter(codigo__in=[n[0] for n in NIVELES])
        }
        result = Counter()
        for codigo, titulo, zona_codigo, nivel_codigo in LABORES:
            _, created = Labor.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "titulo": titulo,
                    "descripcion": f"Labor demo {titulo}.",
                    "zona": zonas[zona_codigo],
                    "nivel": niveles[nivel_codigo],
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_frentes(self):
        labores = {
            labor.codigo: labor
            for labor in Labor.objects.select_related("zona", "nivel").filter(
                codigo__in=[row[0] for row in LABORES]
            )
        }
        result = Counter()
        for codigo, titulo, labor_codigo in FRENTES:
            labor = labores[labor_codigo]
            _, created = LaborFrente.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "titulo": titulo,
                    "descripcion": f"Frente demo {titulo}.",
                    "labor": labor,
                    "zona": labor.zona,
                    "nivel": labor.nivel,
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_grupos(self):
        result = Counter()
        for codigo, nombre in GRUPOS:
            _, created = GrupoPerforacion.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "descripcion": f"{nombre} demo.",
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_integrantes(self):
        trabajadores = {
            trabajador.codigo: trabajador
            for trabajador in Trabajador.objects.filter(codigo__startswith="TRAB")
        }
        grupos = {
            grupo.codigo: grupo
            for grupo in GrupoPerforacion.objects.filter(codigo__in=[row[0] for row in GRUPOS])
        }
        assignments = [
            ("GP-01", "TRAB019", "Perforista lider"),
            ("GP-01", "TRAB020", "Perforista"),
            ("GP-01", "TRAB027", "Ayudante"),
            ("GP-01", "TRAB009", "Operador"),
            ("GP-02", "TRAB021", "Perforista lider"),
            ("GP-02", "TRAB022", "Perforista"),
            ("GP-02", "TRAB028", "Ayudante"),
            ("GP-02", "TRAB010", "Operador"),
            ("GP-03", "TRAB023", "Perforista lider"),
            ("GP-03", "TRAB024", "Perforista"),
            ("GP-03", "TRAB029", "Ayudante"),
            ("GP-03", "TRAB011", "Operador"),
            ("GP-04", "TRAB025", "Perforista lider"),
            ("GP-04", "TRAB026", "Perforista"),
            ("GP-04", "TRAB030", "Ayudante"),
            ("GP-04", "TRAB012", "Operador"),
        ]
        result = Counter()
        for grupo_codigo, trabajador_codigo, rol in assignments:
            integrante, created = GrupoPerforacionIntegrante.objects.get_or_create(
                grupo=grupos[grupo_codigo],
                trabajador=trabajadores[trabajador_codigo],
                defaults={"rol_en_grupo": rol, "is_active": True, "deleted_at": None},
            )
            fields = []
            if integrante.rol_en_grupo != rol:
                integrante.rol_en_grupo = rol
                fields.append("rol_en_grupo")
            if not integrante.is_active:
                integrante.is_active = True
                fields.append("is_active")
            if integrante.deleted_at is not None:
                integrante.deleted_at = None
                fields.append("deleted_at")
            if fields:
                integrante.save(update_fields=fields + ["updated_at"])
            result.add(created)
        return result.as_dict()

    def _seed_explosivos(self):
        unidades = {
            unidad.codigo: unidad
            for unidad in UnidadMedida.objects.filter(
                codigo__in=[row[0] for row in CATALOG_BASE[UnidadMedida]]
            )
        }
        result = Counter()
        for codigo, nombre, unidad_codigo in EXPLOSIVOS:
            _, created = Explosivo.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "unidad_medida": unidades[unidad_codigo],
                    "descripcion": f"Explosivo demo {nombre}.",
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_insumos(self):
        unidades = {
            unidad.codigo: unidad
            for unidad in UnidadMedida.objects.filter(
                codigo__in=[row[0] for row in CATALOG_BASE[UnidadMedida]]
            )
        }
        result = Counter()
        for codigo, nombre, unidad_codigo in INSUMOS:
            _, created = InsumoAccesorio.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "unidad_medida": unidades[unidad_codigo],
                    "descripcion": f"Insumo demo {nombre}.",
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_equipos(self):
        empresas = {
            empresa.codigo: empresa
            for empresa in Empresa.objects.filter(codigo__in=[row[0] for row in EMPRESAS])
        }
        result = Counter()
        for codigo, nombre, tipo, empresa_codigo in EQUIPOS:
            _, created = Equipo.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "tipo": tipo,
                    "empresa": empresas[empresa_codigo],
                    "descripcion": f"Equipo demo {nombre}.",
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_requerimiento_productos(self):
        rubros = {
            rubro.codigo: rubro
            for rubro in RequerimientoRubro.objects.filter(
                codigo__in=[row[3] for row in REQUERIMIENTO_PRODUCTOS],
            )
        }
        unidades = {
            unidad.codigo: unidad
            for unidad in UnidadMedida.objects.filter(
                codigo__in=[row[4] for row in REQUERIMIENTO_PRODUCTOS],
            )
        }
        result = Counter()
        for codigo, nombre, seccion, rubro_codigo, unidad_codigo in REQUERIMIENTO_PRODUCTOS:
            _, created = RequerimientoProducto.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "nombre": nombre,
                    "descripcion": nombre,
                    "seccion": seccion,
                    "rubro": rubros[rubro_codigo],
                    "unidad_medida": unidades[unidad_codigo],
                    "is_active": True,
                    "deleted_at": None,
                },
            )
            result.add(created)
        return result.as_dict()

    def _seed_tipo_cartilla(self):
        result = Counter()
        _, created = TipoCartilla.objects.update_or_create(
            codigo=CARTILLA_CODE,
            defaults={
                "nombre": "Cartilla diaria de operacion mina",
                "descripcion": "Cartilla diaria/por turno para operaciones de mina subterranea.",
                "version": 1,
                "schema_json": json.dumps(CARTILLA_SCHEMA, ensure_ascii=False),
                "is_active": True,
                "deleted_at": None,
            },
        )
        result.add(created)
        _, created = TipoCartilla.objects.update_or_create(
            codigo=REQUERIMIENTO_CARTILLA_CODE,
            defaults={
                "nombre": "Cartilla de requerimiento de productos",
                "descripcion": "Solicitud de herramientas, accesorios, repuestos y EPP por sucursal.",
                "version": 1,
                "schema_json": json.dumps(
                    {
                        "sections": [
                            "datosGenerales",
                            "herramientasOtros",
                            "equipoProteccionPersonal",
                        ],
                    },
                    ensure_ascii=False,
                ),
                "is_active": True,
                "deleted_at": None,
            },
        )
        result.add(created)
        return result.as_dict()

    def _seed_user(self, options):
        if not options["with_user"]:
            return None

        username = options["username"].strip()
        password = options["password"]
        email = options["email"].strip()
        dni = options["dni"].strip()

        if not username:
            raise CommandError("--with-user requiere --username.")
        if not password:
            self.stdout.write(
                self.style.WARNING(
                    "Usuario demo omitido: --with-user requiere --password."
                )
            )
            return None

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "dni": dni or None,
                "is_active": True,
                "is_staff": options["role"] == "admin",
                "is_superuser": options["role"] == "admin",
            },
        )
        user.email = email
        user.dni = dni or None
        user.is_active = True
        user.is_staff = options["role"] == "admin"
        user.is_superuser = options["role"] == "admin"
        user.set_password(password)
        user.save()

        role = Role.objects.get(code=options["role"])
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": role, "is_active": True, "deleted_at": None},
        )
        profile.role = role
        profile.is_active = True
        profile.deleted_at = None
        profile.save()
        user._demo_seed_created = created
        return user

    def _assign_cartilla_if_requested(self, user, options):
        if not options["assign_cartilla"]:
            return None

        username = options["username"].strip()
        if user is None and username:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist as exc:
                raise CommandError(f"Usuario no existe para asignacion: {username}") from exc

        if user is None:
            self.stdout.write(
                self.style.WARNING(
                    "Asignacion omitida: indique --username con --assign-cartilla."
                )
            )
            return None

        tipos = TipoCartilla.objects.filter(
            codigo__in=[CARTILLA_CODE, REQUERIMIENTO_CARTILLA_CODE],
        )
        created_any = False
        for tipo_cartilla in tipos:
            assignment, created = AsignacionCartillaUsuario.objects.get_or_create(
                user=user,
                tipo_cartilla=tipo_cartilla,
                defaults={"estado": AsignacionCartillaUsuario.ESTADO_ACTIVO},
            )
            assignment.estado = AsignacionCartillaUsuario.ESTADO_ACTIVO
            assignment.deleted_at = None
            assignment.save()
            created_any = created_any or created
        return {
            "username": user.username,
            "cartilla": ", ".join(tipos.values_list("codigo", flat=True)),
            "created": created_any,
        }

    def _reset_demo_relations(self):
        now = timezone.now()
        grupos = GrupoPerforacion.objects.filter(codigo__in=[row[0] for row in GRUPOS])
        GrupoPerforacionIntegrante.objects.filter(grupo__in=grupos).update(
            is_active=False,
            deleted_at=now,
        )

    def _counts(self):
        active = {"is_active": True, "deleted_at__isnull": True}
        return {
            "areas": Area.objects.filter(**active).count(),
            "guardias": Guardia.objects.filter(**active).count(),
            "turnos": Turno.objects.filter(**active).count(),
            "climas": Clima.objects.filter(**active).count(),
            "empresas": Empresa.objects.filter(**active).count(),
            "cargos": Cargo.objects.filter(**active).count(),
            "trabajadores": Trabajador.objects.filter(**active).count(),
            "ingenieros": Trabajador.objects.filter(
                **active,
                es_ingeniero_minero=True,
            ).count(),
            "supervisores": Trabajador.objects.filter(
                **active,
                es_supervisor=True,
            ).count(),
            "operadores": Trabajador.objects.filter(**active, es_operador=True).count(),
            "zonas": Zona.objects.filter(**active).count(),
            "niveles": Nivel.objects.filter(**active).count(),
            "labores": Labor.objects.filter(**active).count(),
            "frentes": LaborFrente.objects.filter(**active).count(),
            "grupos_perforacion": GrupoPerforacion.objects.filter(**active).count(),
            "integrantes_grupo": GrupoPerforacionIntegrante.objects.filter(
                **active,
            ).count(),
            "gp_03_integrantes": GrupoPerforacionIntegrante.objects.filter(
                **active,
                grupo__codigo="GP-03",
            ).count(),
            "productos": Producto.objects.filter(**active).count(),
            "unidades_medida": UnidadMedida.objects.filter(**active).count(),
            "explosivos": Explosivo.objects.filter(**active).count(),
            "insumos": InsumoAccesorio.objects.filter(**active).count(),
            "equipos": Equipo.objects.filter(**active).count(),
            "tipo_cartilla": TipoCartilla.objects.filter(
                **active,
                codigo=CARTILLA_CODE,
            ).count(),
            "asignaciones": AsignacionCartillaUsuario.objects.filter(
                estado=AsignacionCartillaUsuario.ESTADO_ACTIVO,
                deleted_at__isnull=True,
                tipo_cartilla__codigo=CARTILLA_CODE,
            ).count(),
        }

    def _validate_bootstrap(self, user):
        if user is None:
            return {"skipped": True, "reason": "sin usuario demo/asignado"}
        payload = catalog_payload()
        tipos = tipos_cartilla_for_user(user)
        return {
            "skipped": False,
            "tipos_cartilla": tipos.count(),
            "incluye_cartilla_mina": tipos.filter(codigo=CARTILLA_CODE).exists(),
            "trabajadores": len(payload["trabajadores"]),
            "frentes": len(payload["labores_frente"]),
            "grupos": len(payload["grupos_perforacion"]),
            "gp_03_integrantes": GrupoPerforacionIntegrante.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
                grupo__codigo="GP-03",
            ).count(),
            "explosivos": len(payload["explosivos"]),
            "insumos": len(payload["insumos_accesorios"]),
            "equipos": len(payload["equipos"]),
        }

    def _print_dry_run(self, options):
        self.stdout.write(self.style.WARNING("DRY RUN: no se escribira en la base."))
        self.stdout.write(f"Areas: {len(CATALOG_BASE[Area])}")
        self.stdout.write(f"Guardias: {len(CATALOG_BASE[Guardia])}")
        self.stdout.write(f"Turnos: {len(TURNOS)}")
        self.stdout.write(f"Trabajadores demo: {len(self._trabajadores_rows())}")
        self.stdout.write(f"Frentes: {len(FRENTES)}")
        self.stdout.write(f"Grupos perforacion: {len(GRUPOS)}")
        self.stdout.write("Password: no se muestra")
        if options["with_user"] and not options["password"]:
            self.stdout.write("Usuario demo: omitido sin --password")

    def _print_summary(self, summary, user, assignment, counts, bootstrap, options):
        self.stdout.write(self.style.SUCCESS("Seed demo Mina completado."))
        for key, value in summary.items():
            self.stdout.write(f"{key}: {value}")

        if user is None:
            self.stdout.write(
                "Usuario demo: omitido. Use --with-user --username mina_test "
                "--password '<password>' --email mina_test@example.com "
                "--assign-cartilla"
            )
        else:
            action = "created" if getattr(user, "_demo_seed_created", False) else "updated"
            self.stdout.write(f"Usuario demo: {user.username} ({action})")
            self.stdout.write("Password: no se muestra")

        self.stdout.write(f"Asignacion cartilla: {assignment or 'omitida'}")
        self.stdout.write(f"Reset demo: {bool(options['reset_demo'])}")
        self.stdout.write("Conteos finales:")
        for key, value in counts.items():
            self.stdout.write(f"  {key}: {value}")
        self.stdout.write(f"Bootstrap validado: {bootstrap}")


class Counter:
    def __init__(self, created=None):
        self.created = 0
        self.updated = 0
        if created is not None:
            self.add(created)

    def add(self, created):
        if created:
            self.created += 1
        else:
            self.updated += 1

    def as_dict(self):
        return {"created": self.created, "updated": self.updated}


def update_or_create_by_codigo(model, codigo, defaults):
    instance = model.objects.filter(codigo=codigo).order_by("id").first()
    if instance is None:
        instance = model(codigo=codigo, **defaults)
        instance.save()
        return instance, True

    for field, value in defaults.items():
        setattr(instance, field, value)
    instance.save()
    return instance, False
