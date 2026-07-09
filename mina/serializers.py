import json

from rest_framework import serializers

from attachments.serializers import AttachmentSerializer

from .models import (
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
    CartillaWorkflowLog,
)
from .workflow import get_available_cartilla_actions


class EmbeddedCatalogSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    codigo = serializers.CharField(read_only=True)
    nombre = serializers.SerializerMethodField()

    def get_nombre(self, obj):
        return (
            getattr(obj, "nombre", "")
            or getattr(obj, "razon_social", "")
            or getattr(obj, "titulo", "")
            or str(obj)
        )


class EmbeddedTrabajadorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    codigo = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    dni = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    nombres = serializers.CharField(read_only=True)
    apellidos = serializers.CharField(read_only=True)


class EmbeddedTipoCartillaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    codigo = serializers.CharField(read_only=True)
    nombre = serializers.CharField(read_only=True)


class CartillaMinaListSerializer(serializers.ModelSerializer):
    clientRecordId = serializers.CharField(source="client_record_id", read_only=True)
    tipoCartilla = EmbeddedTipoCartillaSerializer(source="tipo_cartilla", read_only=True)
    fechaOperacion = serializers.DateField(source="fecha_operacion", read_only=True)
    turno = EmbeddedCatalogSerializer(read_only=True)
    guardia = EmbeddedCatalogSerializer(read_only=True)
    area = EmbeddedCatalogSerializer(read_only=True)
    zona = EmbeddedCatalogSerializer(read_only=True)
    nivel = EmbeddedCatalogSerializer(read_only=True)
    ingenieroMinero = EmbeddedTrabajadorSerializer(
        source="ingeniero_minero",
        read_only=True,
    )
    supervisor = EmbeddedTrabajadorSerializer(read_only=True)
    clima = EmbeddedCatalogSerializer(read_only=True)
    sucursal = EmbeddedCatalogSerializer(read_only=True)
    responsableRequerimiento = EmbeddedTrabajadorSerializer(
        source="responsable_requerimiento",
        read_only=True,
    )
    estadoWorkflow = serializers.CharField(source="estado_workflow", read_only=True)
    syncStatus = serializers.CharField(source="sync_status", read_only=True)
    attachmentsCount = serializers.IntegerField(source="attachments_count", read_only=True)
    availableActions = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = CartillaOperacionMina
        fields = (
            "id",
            "clientRecordId",
            "tipoCartilla",
            "fechaOperacion",
            "turno",
            "guardia",
            "area",
            "zona",
            "nivel",
            "ingenieroMinero",
            "supervisor",
            "clima",
            "sucursal",
            "responsableRequerimiento",
            "estadoWorkflow",
            "syncStatus",
            "attachmentsCount",
            "availableActions",
            "createdAt",
            "updatedAt",
        )

    def get_availableActions(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return {}
        return get_available_cartilla_actions(obj, request.user)


class PerforacionExplosivoSerializer(serializers.ModelSerializer):
    explosivo = EmbeddedCatalogSerializer(read_only=True)
    unidadMedida = EmbeddedCatalogSerializer(source="unidad_medida", read_only=True)

    class Meta:
        model = CartillaPerforacionExplosivo
        fields = ("id", "row_key", "explosivo", "cantidad", "unidadMedida")


class PerforacionInsumoSerializer(serializers.ModelSerializer):
    insumo = EmbeddedCatalogSerializer(read_only=True)
    unidadMedida = EmbeddedCatalogSerializer(source="unidad_medida", read_only=True)

    class Meta:
        model = CartillaPerforacionInsumo
        fields = ("id", "row_key", "insumo", "cantidad", "unidadMedida")


class PerforacionVoladuraSerializer(serializers.ModelSerializer):
    grupoPerforacion = EmbeddedCatalogSerializer(
        source="grupo_perforacion",
        read_only=True,
    )
    producto = EmbeddedCatalogSerializer(read_only=True)
    laborFrente = EmbeddedCatalogSerializer(source="labor_frente", read_only=True)
    seccionAncho = serializers.DecimalField(
        source="seccion_ancho",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    seccionAlto = serializers.DecimalField(
        source="seccion_alto",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    horaInicio = serializers.TimeField(source="hora_inicio", read_only=True)
    horaTermino = serializers.TimeField(source="hora_termino", read_only=True)
    explosivos = PerforacionExplosivoSerializer(many=True, read_only=True)
    insumos = PerforacionInsumoSerializer(many=True, read_only=True)

    class Meta:
        model = CartillaPerforacionVoladura
        fields = (
            "id",
            "row_key",
            "grupoPerforacion",
            "producto",
            "seccionAncho",
            "seccionAlto",
            "horaInicio",
            "horaTermino",
            "taladros",
            "laborFrente",
            "observaciones",
            "explosivos",
            "insumos",
        )


class ExtraccionAcarreoSerializer(serializers.ModelSerializer):
    producto = EmbeddedCatalogSerializer(read_only=True)
    equipo = EmbeddedCatalogSerializer(read_only=True)
    operador = EmbeddedTrabajadorSerializer(read_only=True)
    origenTexto = serializers.CharField(source="origen_texto", read_only=True)
    destinoTexto = serializers.CharField(source="destino_texto", read_only=True)

    class Meta:
        model = CartillaExtraccionAcarreo
        fields = (
            "id",
            "row_key",
            "producto",
            "origenTexto",
            "destinoTexto",
            "toneladas",
            "viajes",
            "equipo",
            "operador",
            "observaciones",
        )


class PersonalSerializer(serializers.ModelSerializer):
    trabajador = EmbeddedTrabajadorSerializer(read_only=True)
    cargo = EmbeddedCatalogSerializer(read_only=True)
    empresa = EmbeddedCatalogSerializer(read_only=True)
    horaIngreso = serializers.TimeField(source="hora_ingreso", read_only=True)
    horaSalida = serializers.TimeField(source="hora_salida", read_only=True)

    class Meta:
        model = CartillaPersonal
        fields = (
            "id",
            "row_key",
            "trabajador",
            "cargo",
            "empresa",
            "horaIngreso",
            "horaSalida",
            "epp",
            "observaciones",
        )


class EquipoSerializer(serializers.ModelSerializer):
    equipo = EmbeddedCatalogSerializer(read_only=True)
    operador = EmbeddedTrabajadorSerializer(read_only=True)
    codigoEquipoSnapshot = serializers.CharField(
        source="codigo_equipo_snapshot",
        read_only=True,
    )
    horaInicio = serializers.TimeField(source="hora_inicio", read_only=True)
    horaFin = serializers.TimeField(source="hora_fin", read_only=True)
    horometroInicial = serializers.DecimalField(
        source="horometro_inicial",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    horometroFinal = serializers.DecimalField(
        source="horometro_final",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    totalHoras = serializers.DecimalField(
        source="total_horas",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = CartillaEquipo
        fields = (
            "id",
            "row_key",
            "equipo",
            "codigoEquipoSnapshot",
            "operador",
            "horaInicio",
            "horaFin",
            "horometroInicial",
            "horometroFinal",
            "combustible",
            "totalHoras",
            "observaciones",
        )


class AvanceSerializer(serializers.ModelSerializer):
    laborFrente = EmbeddedCatalogSerializer(source="labor_frente", read_only=True)
    avanceDia = serializers.DecimalField(
        source="avance_dia",
        max_digits=12,
        decimal_places=3,
        read_only=True,
    )
    condicionesFrente = serializers.CharField(
        source="condiciones_frente",
        read_only=True,
    )

    class Meta:
        model = CartillaAvance
        fields = (
            "id",
            "row_key",
            "laborFrente",
            "tipo",
            "meta",
            "avanceDia",
            "acumulado",
            "condicionesFrente",
            "actividades",
            "observaciones",
        )


class AccionCorrectivaSerializer(serializers.ModelSerializer):
    responsable = EmbeddedTrabajadorSerializer(read_only=True)

    class Meta:
        model = CartillaAccionCorrectiva
        fields = (
            "id",
            "row_key",
            "descripcion",
            "responsable",
            "plazo",
            "estado",
            "observaciones",
        )


class RequerimientoProductoDetalleSerializer(serializers.ModelSerializer):
    rubro = EmbeddedCatalogSerializer(read_only=True)
    producto = EmbeddedCatalogSerializer(read_only=True)
    unidadMedida = EmbeddedCatalogSerializer(source="unidad_medida", read_only=True)

    class Meta:
        model = CartillaRequerimientoProductoDetalle
        fields = (
            "id",
            "row_key",
            "seccion",
            "fecha",
            "rubro",
            "producto",
            "descripcion",
            "cantidad",
            "unidadMedida",
            "prioridad",
        )


class WorkflowLogSerializer(serializers.ModelSerializer):
    fromState = serializers.CharField(source="from_state", read_only=True)
    toState = serializers.CharField(source="to_state", read_only=True)
    createdById = serializers.IntegerField(source="created_by_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = CartillaWorkflowLog
        fields = ("id", "fromState", "toState", "action", "comment", "createdById", "createdAt")


class CartillaMinaDetailSerializer(CartillaMinaListSerializer):
    dataJson = serializers.SerializerMethodField()
    dataJsonWarning = serializers.SerializerMethodField()
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, read_only=True)
    lon = serializers.DecimalField(max_digits=9, decimal_places=6, read_only=True)
    syncAttempts = serializers.IntegerField(source="sync_attempts", read_only=True)
    syncError = serializers.CharField(source="sync_error", read_only=True)
    perforacionVoladura = PerforacionVoladuraSerializer(
        source="perforaciones_voladura",
        many=True,
        read_only=True,
    )
    extraccionAcarreo = ExtraccionAcarreoSerializer(
        source="extracciones_acarreo",
        many=True,
        read_only=True,
    )
    personal = PersonalSerializer(many=True, read_only=True)
    equipos = EquipoSerializer(many=True, read_only=True)
    avances = AvanceSerializer(many=True, read_only=True)
    accionesCorrectivas = AccionCorrectivaSerializer(
        source="acciones_correctivas",
        many=True,
        read_only=True,
    )
    requerimientoProductos = RequerimientoProductoDetalleSerializer(
        source="requerimiento_productos",
        many=True,
        read_only=True,
    )
    attachments = serializers.SerializerMethodField()
    workflowLogs = WorkflowLogSerializer(
        source="workflow_logs",
        many=True,
        read_only=True,
    )
    submittedAt = serializers.DateTimeField(source="submitted_at", read_only=True)
    reviewedAt = serializers.DateTimeField(source="reviewed_at", read_only=True)
    closedAt = serializers.DateTimeField(source="closed_at", read_only=True)

    class Meta(CartillaMinaListSerializer.Meta):
        fields = CartillaMinaListSerializer.Meta.fields + (
            "lat",
            "lon",
            "syncAttempts",
            "syncError",
            "dataJson",
            "dataJsonWarning",
            "perforacionVoladura",
            "extraccionAcarreo",
            "personal",
            "equipos",
            "avances",
            "accionesCorrectivas",
            "requerimientoProductos",
            "attachments",
            "workflowLogs",
            "submittedAt",
            "reviewedAt",
            "closedAt",
        )

    def get_dataJson(self, obj):
        raw = obj.data_json or "{}"
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return raw

    def get_dataJsonWarning(self, obj):
        if not obj.data_json:
            return ""
        try:
            json.loads(obj.data_json)
        except (TypeError, ValueError):
            return "data_json no contiene JSON valido; se devuelve como texto."
        return ""

    def get_attachments(self, obj):
        attachments = [
            attachment
            for attachment in obj.attachments.all()
            if attachment.deleted_at is None
        ]
        return AttachmentSerializer(
            attachments,
            many=True,
            context=self.context,
        ).data


def _catalog_name(obj):
    if obj is None:
        return ""
    return (
        getattr(obj, "nombre", "")
        or getattr(obj, "razon_social", "")
        or getattr(obj, "titulo", "")
        or str(obj)
    )


def _parse_data_json(obj):
    raw = obj.data_json or "{}"
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}, ["data_json no contiene JSON valido."]
    if not isinstance(parsed, dict):
        return {}, ["data_json debe ser un objeto JSON."]
    return parsed, []


def _active_attachments(obj):
    return [
        attachment
        for attachment in obj.attachments.all()
        if attachment.deleted_at is None
    ]


def _count_related(obj, related_name):
    manager = getattr(obj, related_name)
    if hasattr(manager, "all"):
        return len(manager.all())
    return 0


def _table_snapshot_warnings(snapshot, counts):
    warnings = []
    module_map = {
        "perforacionVoladura": "perforacionVoladura",
        "extraccionAcarreo": "extraccionAcarreo",
        "personal": "personal",
        "equipos": "equipos",
        "avances": "avances",
        "accionesCorrectivas": "accionesCorrectivas",
        "herramientasOtros": "herramientasOtros",
        "equipoProteccionPersonal": "equipoProteccionPersonal",
    }
    for snapshot_key, count_key in module_map.items():
        snapshot_rows = snapshot.get(snapshot_key, [])
        if snapshot_rows in (None, ""):
            snapshot_rows = []
        if isinstance(snapshot_rows, list) and len(snapshot_rows) != counts[count_key]:
            warnings.append(
                (
                    f"{snapshot_key}: dataJson tiene {len(snapshot_rows)} filas "
                    f"y tablas reportables tienen {counts[count_key]}."
                ),
            )
    return warnings


class CartillaMinaSummarySerializer(serializers.ModelSerializer):
    clientRecordId = serializers.CharField(source="client_record_id", read_only=True)
    fechaOperacion = serializers.DateField(source="fecha_operacion", read_only=True)
    turno = serializers.SerializerMethodField()
    guardia = serializers.SerializerMethodField()
    area = serializers.SerializerMethodField()
    sucursal = serializers.SerializerMethodField()
    responsableRequerimiento = serializers.SerializerMethodField()
    estadoWorkflow = serializers.CharField(source="estado_workflow", read_only=True)
    syncStatus = serializers.CharField(source="sync_status", read_only=True)
    counts = serializers.SerializerMethodField()
    availableActions = serializers.SerializerMethodField()
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = CartillaOperacionMina
        fields = (
            "id",
            "clientRecordId",
            "fechaOperacion",
            "turno",
            "guardia",
            "area",
            "sucursal",
            "responsableRequerimiento",
            "estadoWorkflow",
            "syncStatus",
            "counts",
            "availableActions",
            "updatedAt",
        )

    def get_turno(self, obj):
        return _catalog_name(obj.turno)

    def get_guardia(self, obj):
        return _catalog_name(obj.guardia)

    def get_area(self, obj):
        return _catalog_name(obj.area)

    def get_sucursal(self, obj):
        return _catalog_name(obj.sucursal)

    def get_responsableRequerimiento(self, obj):
        if obj.responsable_requerimiento_id:
            return str(obj.responsable_requerimiento)
        return ""

    def get_counts(self, obj):
        return {
            "perforacionVoladura": _count_related(obj, "perforaciones_voladura"),
            "extraccionAcarreo": _count_related(obj, "extracciones_acarreo"),
            "personal": _count_related(obj, "personal"),
            "equipos": _count_related(obj, "equipos"),
            "avances": _count_related(obj, "avances"),
            "accionesCorrectivas": _count_related(obj, "acciones_correctivas"),
            "requerimientoProductos": _count_related(obj, "requerimiento_productos"),
            "attachments": len(_active_attachments(obj)),
        }

    def get_availableActions(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return {}
        return get_available_cartilla_actions(obj, request.user)


class CartillaMinaRenderDataSerializer(serializers.Serializer):
    def to_representation(self, obj):
        snapshot, warnings = _parse_data_json(obj)
        counts = CartillaMinaSummarySerializer(
            obj,
            context=self.context,
        ).data["counts"]
        warnings.extend(_table_snapshot_warnings(snapshot, counts))

        header = {
            "fechaOperacion": obj.fecha_operacion,
            "tipoCartilla": EmbeddedTipoCartillaSerializer(obj.tipo_cartilla).data,
            "turno": EmbeddedCatalogSerializer(obj.turno).data,
            "guardia": EmbeddedCatalogSerializer(obj.guardia).data,
            "area": EmbeddedCatalogSerializer(obj.area).data,
            "zona": EmbeddedCatalogSerializer(obj.zona).data if obj.zona_id else None,
            "nivel": EmbeddedCatalogSerializer(obj.nivel).data if obj.nivel_id else None,
            "ingenieroMinero": (
                EmbeddedTrabajadorSerializer(obj.ingeniero_minero).data
                if obj.ingeniero_minero_id
                else None
            ),
            "supervisor": (
                EmbeddedTrabajadorSerializer(obj.supervisor).data
                if obj.supervisor_id
                else None
            ),
            "clima": EmbeddedCatalogSerializer(obj.clima).data if obj.clima_id else None,
            "sucursal": (
                EmbeddedCatalogSerializer(obj.sucursal).data if obj.sucursal_id else None
            ),
            "responsableRequerimiento": (
                EmbeddedTrabajadorSerializer(obj.responsable_requerimiento).data
                if obj.responsable_requerimiento_id
                else None
            ),
            "estadoWorkflow": obj.estado_workflow,
            "syncStatus": obj.sync_status,
            "submittedAt": obj.submitted_at,
            "reviewedAt": obj.reviewed_at,
            "closedAt": obj.closed_at,
        }

        modules = {
            "datosGenerales": snapshot.get("datosGenerales", {}),
            "perforacionVoladura": PerforacionVoladuraSerializer(
                obj.perforaciones_voladura.all(),
                many=True,
            ).data,
            "extraccionAcarreo": ExtraccionAcarreoSerializer(
                obj.extracciones_acarreo.all(),
                many=True,
            ).data,
            "personal": PersonalSerializer(obj.personal.all(), many=True).data,
            "equipos": EquipoSerializer(obj.equipos.all(), many=True).data,
            "avances": AvanceSerializer(obj.avances.all(), many=True).data,
            "accionesCorrectivas": AccionCorrectivaSerializer(
                obj.acciones_correctivas.all(),
                many=True,
            ).data,
            "herramientasOtros": RequerimientoProductoDetalleSerializer(
                obj.requerimiento_productos.filter(
                    seccion=CartillaRequerimientoProductoDetalle.SECCION_HERRAMIENTAS,
                ),
                many=True,
            ).data,
            "equipoProteccionPersonal": RequerimientoProductoDetalleSerializer(
                obj.requerimiento_productos.filter(
                    seccion=CartillaRequerimientoProductoDetalle.SECCION_EPP,
                ),
                many=True,
            ).data,
            "observaciones": snapshot.get("observaciones", []),
            "firmas": snapshot.get("firmas", []),
        }

        request = self.context.get("request")
        available_actions = (
            get_available_cartilla_actions(obj, request.user)
            if request and request.user and request.user.is_authenticated
            else {}
        )

        return {
            "id": obj.pk,
            "clientRecordId": obj.client_record_id,
            "header": header,
            "modules": modules,
            "attachments": AttachmentSerializer(
                _active_attachments(obj),
                many=True,
                context=self.context,
            ).data,
            "workflowLogs": WorkflowLogSerializer(
                obj.workflow_logs.all(),
                many=True,
            ).data,
            "availableActions": available_actions,
            "warnings": warnings,
        }
