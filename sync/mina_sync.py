import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from rest_framework import serializers

from catalogos.models import (
    Cargo,
    Equipo,
    Empresa,
    Explosivo,
    GrupoPerforacion,
    InsumoAccesorio,
    LaborFrente,
    Producto,
    RequerimientoProducto,
    RequerimientoRubro,
    Trabajador,
    UnidadMedida,
)
from mina.models import (
    CartillaAccionCorrectiva,
    CartillaAvance,
    CartillaEquipo,
    CartillaExtraccionAcarreo,
    CartillaOperacionMina,
    CartillaPerforacionExplosivo,
    CartillaPerforacionInsumo,
    CartillaPerforacionVoladura,
    CartillaPersonal,
    CartillaRequerimientoProductoDetalle,
)
from sync.serializers import CARTILLA_REQUERIMIENTO_PRODUCTOS


REQUERIMIENTO_SECTION_MAP = {
    "herramientasOtros": CartillaRequerimientoProductoDetalle.SECCION_HERRAMIENTAS,
    "equipoProteccionPersonal": CartillaRequerimientoProductoDetalle.SECCION_EPP,
}


class MinaCartillaSyncService:
    def __init__(self, user, validated_data):
        self.user = user
        self.data = validated_data
        self.warnings = []

    @transaction.atomic
    def sync(self):
        cartilla, created = self._upsert_cartilla()
        self._replace_children(cartilla)

        return {
            "clientRecordId": cartilla.client_record_id,
            "serverCartillaId": cartilla.pk,
            "syncStatus": cartilla.sync_status,
            "estadoWorkflow": cartilla.estado_workflow,
            "created": created,
            "updatedAt": cartilla.updated_at,
            "warnings": self.warnings,
        }

    def _upsert_cartilla(self):
        client_record_id = self.data["clientRecordId"]
        existing = CartillaOperacionMina.objects.filter(
            user=self.user,
            client_record_id=client_record_id,
        ).first()
        created = existing is None
        cartilla = existing or CartillaOperacionMina(
            user=self.user,
            client_record_id=client_record_id,
        )

        cartilla.tipo_cartilla = self.data["tipo_cartilla"]
        cartilla.fecha_operacion = self.data["fechaOperacion"]
        cartilla.turno = self.data["turno"]
        cartilla.guardia = self.data["guardia"]
        cartilla.area = self.data["area"]
        cartilla.zona = self.data.get("zona")
        cartilla.nivel = self.data.get("nivel")
        cartilla.ingeniero_minero = self.data.get("ingeniero_minero")
        cartilla.supervisor = self.data.get("supervisor")
        cartilla.clima = self.data.get("clima")
        cartilla.sucursal = self.data.get("sucursal")
        cartilla.responsable_requerimiento = self.data.get("responsable_requerimiento")
        cartilla.estado_workflow = self.data["estado"]
        cartilla.sync_status = CartillaOperacionMina.SYNC_SYNCED
        cartilla.sync_error = ""
        cartilla.sync_attempts = (cartilla.sync_attempts or 0) + 1
        cartilla.data_json = json.dumps(
            self.data["dataJson"],
            ensure_ascii=False,
            sort_keys=True,
        )
        cartilla.lat = self.data.get("lat")
        cartilla.lon = self.data.get("lon")
        if self.data["estado"] == CartillaOperacionMina.ESTADO_ENVIADO:
            cartilla.submitted_at = cartilla.submitted_at or timezone.now()
        cartilla.save()
        return cartilla, created

    def _replace_children(self, cartilla):
        self._delete_existing_children(cartilla)
        data_json = self.data["dataJson"]

        if self.data["cartillaType"] == CARTILLA_REQUERIMIENTO_PRODUCTOS:
            self._create_requerimiento_productos(cartilla, data_json)
            return

        self._create_perforaciones(cartilla, data_json.get("perforacionVoladura", []))
        self._create_extracciones(cartilla, data_json.get("extraccionAcarreo", []))
        self._create_personal(cartilla, data_json.get("personal", []))
        self._create_equipos(cartilla, data_json.get("equipos", []))
        self._create_avances(cartilla, data_json.get("avances", []))
        self._create_acciones(cartilla, data_json.get("accionesCorrectivas", []))

    def _delete_existing_children(self, cartilla):
        cartilla.perforaciones_voladura.all().delete()
        cartilla.extracciones_acarreo.all().delete()
        cartilla.personal.all().delete()
        cartilla.equipos.all().delete()
        cartilla.avances.all().delete()
        cartilla.acciones_correctivas.all().delete()
        cartilla.requerimiento_productos.all().delete()

    def _create_requerimiento_productos(self, cartilla, data_json):
        for module_key, seccion in REQUERIMIENTO_SECTION_MAP.items():
            for index, row in enumerate(self._rows(data_json.get(module_key, []))):
                missing = self._missing_required(
                    row,
                    (
                        "fecha",
                        "rubroId",
                        "productoId",
                        "cantidad",
                        "unidadMedidaId",
                        "prioridad",
                    ),
                )
                if missing:
                    self._handle_incomplete_row(module_key, index, missing)
                    continue

                CartillaRequerimientoProductoDetalle.objects.create(
                    cartilla=cartilla,
                    row_key=row["rowKey"],
                    seccion=seccion,
                    fecha=self._date(row["fecha"]),
                    rubro=self._catalog(
                        RequerimientoRubro,
                        row["rubroId"],
                        module_key,
                        index,
                        "rubroId",
                    ),
                    producto=self._catalog(
                        RequerimientoProducto,
                        row["productoId"],
                        module_key,
                        index,
                        "productoId",
                    ),
                    descripcion=row.get("descripcion", "") or "",
                    cantidad=self._decimal(row["cantidad"], "cantidad"),
                    unidad_medida=self._catalog(
                        UnidadMedida,
                        row["unidadMedidaId"],
                        module_key,
                        index,
                        "unidadMedidaId",
                    ),
                    prioridad=row["prioridad"],
                )

    def _create_perforaciones(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            missing = self._missing_required(
                row,
                (
                    "grupoPerforacionId",
                    "productoId",
                    "seccionAncho",
                    "seccionAlto",
                    "horaInicio",
                    "horaTermino",
                    "taladros",
                    "laborFrenteId",
                ),
            )
            if missing:
                self._handle_incomplete_row("perforacionVoladura", index, missing)
                continue

            perforacion = CartillaPerforacionVoladura.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                grupo_perforacion=self._catalog(
                    GrupoPerforacion,
                    row["grupoPerforacionId"],
                    "perforacionVoladura",
                    index,
                    "grupoPerforacionId",
                ),
                producto=self._catalog(
                    Producto,
                    row["productoId"],
                    "perforacionVoladura",
                    index,
                    "productoId",
                ),
                seccion_ancho=self._decimal(row["seccionAncho"], "seccionAncho"),
                seccion_alto=self._decimal(row["seccionAlto"], "seccionAlto"),
                hora_inicio=self._time(row["horaInicio"], "horaInicio"),
                hora_termino=self._time(row["horaTermino"], "horaTermino"),
                taladros=row["taladros"],
                labor_frente=self._catalog(
                    LaborFrente,
                    row["laborFrenteId"],
                    "perforacionVoladura",
                    index,
                    "laborFrenteId",
                ),
                observaciones=row.get("observaciones", "") or "",
            )
            self._create_explosivos(
                perforacion,
                row.get("explosivos", []),
                parent_index=index,
            )
            self._create_insumos(perforacion, row.get("insumos", []), parent_index=index)

    def _create_explosivos(self, perforacion, rows, parent_index):
        for index, row in enumerate(self._rows(rows)):
            missing = self._missing_required(row, ("explosivoId", "cantidad", "unidadMedidaId"))
            if missing:
                self._handle_incomplete_row(
                    f"perforacionVoladura[{parent_index}].explosivos",
                    index,
                    missing,
                )
                continue

            CartillaPerforacionExplosivo.objects.create(
                perforacion=perforacion,
                row_key=row["rowKey"],
                explosivo=self._catalog(
                    Explosivo,
                    row["explosivoId"],
                    "explosivos",
                    index,
                    "explosivoId",
                ),
                cantidad=self._decimal(row["cantidad"], "cantidad"),
                unidad_medida=self._catalog(
                    UnidadMedida,
                    row["unidadMedidaId"],
                    "explosivos",
                    index,
                    "unidadMedidaId",
                ),
            )

    def _create_insumos(self, perforacion, rows, parent_index):
        for index, row in enumerate(self._rows(rows)):
            missing = self._missing_required(row, ("insumoId", "cantidad", "unidadMedidaId"))
            if missing:
                self._handle_incomplete_row(
                    f"perforacionVoladura[{parent_index}].insumos",
                    index,
                    missing,
                )
                continue

            CartillaPerforacionInsumo.objects.create(
                perforacion=perforacion,
                row_key=row["rowKey"],
                insumo=self._catalog(
                    InsumoAccesorio,
                    row["insumoId"],
                    "insumos",
                    index,
                    "insumoId",
                ),
                cantidad=self._decimal(row["cantidad"], "cantidad"),
                unidad_medida=self._catalog(
                    UnidadMedida,
                    row["unidadMedidaId"],
                    "insumos",
                    index,
                    "unidadMedidaId",
                ),
            )

    def _create_extracciones(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            CartillaExtraccionAcarreo.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                producto=self._catalog_if_present(
                    Producto,
                    row.get("productoId"),
                    "extraccionAcarreo",
                    index,
                    "productoId",
                ),
                origen_texto=row.get("origenTexto", "") or row.get("origen", "") or "",
                destino_texto=row.get("destinoTexto", "") or row.get("destino", "") or "",
                toneladas=self._optional_decimal(row.get("toneladas")),
                viajes=row.get("viajes"),
                equipo=self._catalog_if_present(
                    Equipo,
                    row.get("equipoId"),
                    "extraccionAcarreo",
                    index,
                    "equipoId",
                ),
                operador=self._catalog_if_present(
                    Trabajador,
                    row.get("operadorId"),
                    "extraccionAcarreo",
                    index,
                    "operadorId",
                ),
                observaciones=row.get("observaciones", "") or "",
            )

    def _create_personal(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            if not row.get("trabajadorId"):
                self._handle_incomplete_row("personal", index, ("trabajadorId",))
                continue
            CartillaPersonal.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                trabajador=self._catalog(
                    Trabajador,
                    row["trabajadorId"],
                    "personal",
                    index,
                    "trabajadorId",
                ),
                cargo=self._catalog_if_present(Cargo, row.get("cargoId"), "personal", index, "cargoId"),
                empresa=self._catalog_if_present(
                    Empresa,
                    row.get("empresaId"),
                    "personal",
                    index,
                    "empresaId",
                ),
                hora_ingreso=self._optional_time(row.get("horaIngreso")),
                hora_salida=self._optional_time(row.get("horaSalida")),
                epp=row.get("epp", True),
                observaciones=row.get("observaciones", "") or "",
            )

    def _create_equipos(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            if not row.get("equipoId"):
                self._handle_incomplete_row("equipos", index, ("equipoId",))
                continue
            equipo = self._catalog(Equipo, row["equipoId"], "equipos", index, "equipoId")
            CartillaEquipo.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                equipo=equipo,
                codigo_equipo_snapshot=row.get("codigo", "") or equipo.codigo,
                operador=self._catalog_if_present(
                    Trabajador,
                    row.get("operadorId"),
                    "equipos",
                    index,
                    "operadorId",
                ),
                hora_inicio=self._optional_time(row.get("horaInicio")),
                hora_fin=self._optional_time(row.get("horaFin")),
                horometro_inicial=self._optional_decimal(row.get("horometroInicial")),
                horometro_final=self._optional_decimal(row.get("horometroFinal")),
                combustible=self._optional_decimal(row.get("combustible")),
                total_horas=self._optional_decimal(row.get("totalHoras")),
                observaciones=row.get("observaciones", "") or "",
            )

    def _create_avances(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            CartillaAvance.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                labor_frente=self._catalog_if_present(
                    LaborFrente,
                    row.get("laborFrenteId"),
                    "avances",
                    index,
                    "laborFrenteId",
                ),
                tipo=row.get("tipo", "") or "",
                meta=self._optional_decimal(row.get("meta")),
                avance_dia=self._optional_decimal(row.get("avanceDia")),
                acumulado=self._optional_decimal(row.get("acumulado")),
                condiciones_frente=row.get("condicionesFrente", "") or "",
                actividades=row.get("actividades", "") or "",
                observaciones=row.get("observaciones", "") or "",
            )

    def _create_acciones(self, cartilla, rows):
        for index, row in enumerate(self._rows(rows)):
            if not row.get("descripcion"):
                self._handle_incomplete_row("accionesCorrectivas", index, ("descripcion",))
                continue
            CartillaAccionCorrectiva.objects.create(
                cartilla=cartilla,
                row_key=row["rowKey"],
                descripcion=row["descripcion"],
                responsable=self._catalog_if_present(
                    Trabajador,
                    row.get("responsableId"),
                    "accionesCorrectivas",
                    index,
                    "responsableId",
                ),
                plazo=self._optional_date(row.get("plazo")),
                estado=row.get("estado", "") or "",
                observaciones=row.get("observaciones", "") or "",
            )

    def _rows(self, value):
        if value in (None, ""):
            return []
        return value

    def _missing_required(self, row, fields):
        return tuple(field for field in fields if row.get(field) in (None, ""))

    def _handle_incomplete_row(self, module, index, missing):
        message = f"{module}[{index}] omitido: faltan {', '.join(missing)}."
        if self.data["estado"] == CartillaOperacionMina.ESTADO_ENVIADO:
            raise serializers.ValidationError({"dataJson": message})
        self.warnings.append(message)

    def _catalog(self, model, value, module, index, field_name):
        obj = self._optional_catalog(model, value)
        if obj is None:
            raise serializers.ValidationError(
                {"dataJson": f"{module}[{index}].{field_name} no existe o esta inactivo."},
            )
        return obj

    def _catalog_if_present(self, model, value, module, index, field_name):
        if value in (None, ""):
            return None
        return self._catalog(model, value, module, index, field_name)

    def _optional_catalog(self, model, value):
        if value in (None, ""):
            return None
        return model.objects.filter(
            pk=value,
            is_active=True,
            deleted_at__isnull=True,
        ).first()

    def _decimal(self, value, field_name):
        parsed = self._optional_decimal(value)
        if parsed is None:
            raise serializers.ValidationError({field_name: "Numero invalido."})
        return parsed

    def _optional_decimal(self, value):
        if value in (None, ""):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise serializers.ValidationError({"dataJson": "Numero decimal invalido."}) from exc

    def _time(self, value, field_name):
        parsed = self._optional_time(value)
        if parsed is None:
            raise serializers.ValidationError({field_name: "Hora invalida."})
        return parsed

    def _optional_time(self, value):
        if value in (None, ""):
            return None
        parsed = parse_time(str(value))
        if parsed is None:
            raise serializers.ValidationError({"dataJson": f"Hora invalida: {value}."})
        return parsed

    def _optional_date(self, value):
        if value in (None, ""):
            return None
        parsed = parse_date(str(value))
        if parsed is None:
            raise serializers.ValidationError({"dataJson": f"Fecha invalida: {value}."})
        return parsed

    def _date(self, value):
        parsed = self._optional_date(value)
        if parsed is None:
            raise serializers.ValidationError({"dataJson": "Fecha invalida."})
        return parsed
