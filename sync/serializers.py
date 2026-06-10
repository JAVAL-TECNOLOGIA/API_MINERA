from rest_framework import serializers

from cartillas.models import TipoCartilla
from catalogos.models import Area, Clima, Guardia, Nivel, Trabajador, Turno, Zona
from mina.models import CartillaOperacionMina


class CartillaOperacionMinaSyncRequestSerializer(serializers.Serializer):
    clientRecordId = serializers.CharField(max_length=64)
    cartillaType = serializers.CharField(max_length=50)
    payloadVersion = serializers.IntegerField(min_value=1)
    fechaOperacion = serializers.DateField()
    turnoId = serializers.IntegerField()
    guardiaId = serializers.IntegerField()
    areaId = serializers.IntegerField()
    zonaId = serializers.IntegerField(required=False, allow_null=True)
    nivelId = serializers.IntegerField(required=False, allow_null=True)
    ingenieroMineroId = serializers.IntegerField(required=False, allow_null=True)
    supervisorId = serializers.IntegerField(required=False, allow_null=True)
    climaId = serializers.IntegerField(required=False, allow_null=True)
    estado = serializers.ChoiceField(
        choices=[
            CartillaOperacionMina.ESTADO_BORRADOR,
            CartillaOperacionMina.ESTADO_ENVIADO,
        ],
    )
    lat = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    lon = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    dataJson = serializers.JSONField()

    def validate(self, attrs):
        attrs["tipo_cartilla"] = self._get_active(
            TipoCartilla,
            "cartillaType",
            codigo=attrs["cartillaType"],
        )
        attrs["turno"] = self._get_active(Turno, "turnoId", pk=attrs["turnoId"])
        attrs["guardia"] = self._get_active(Guardia, "guardiaId", pk=attrs["guardiaId"])
        attrs["area"] = self._get_active(Area, "areaId", pk=attrs["areaId"])
        attrs["zona"] = self._get_optional_active(Zona, "zonaId", attrs.get("zonaId"))
        attrs["nivel"] = self._get_optional_active(Nivel, "nivelId", attrs.get("nivelId"))
        attrs["ingeniero_minero"] = self._get_optional_active(
            Trabajador,
            "ingenieroMineroId",
            attrs.get("ingenieroMineroId"),
        )
        attrs["supervisor"] = self._get_optional_active(
            Trabajador,
            "supervisorId",
            attrs.get("supervisorId"),
        )
        attrs["clima"] = self._get_optional_active(Clima, "climaId", attrs.get("climaId"))

        data_json = attrs["dataJson"]
        if not isinstance(data_json, dict):
            raise serializers.ValidationError({"dataJson": "Debe ser un objeto JSON."})

        self._validate_repeatable_rows(data_json)
        if attrs["estado"] == CartillaOperacionMina.ESTADO_ENVIADO:
            self._validate_sent_payload(data_json)

        return attrs

    def _get_active(self, model, field_name, **lookup):
        try:
            return model.objects.get(
                is_active=True,
                deleted_at__isnull=True,
                **lookup,
            )
        except model.DoesNotExist as exc:
            raise serializers.ValidationError(
                {field_name: "No existe o esta inactivo."},
            ) from exc

    def _get_optional_active(self, model, field_name, value):
        if value in (None, ""):
            return None
        return self._get_active(model, field_name, pk=value)

    def _validate_repeatable_rows(self, data_json):
        for module_key in (
            "perforacionVoladura",
            "extraccionAcarreo",
            "personal",
            "equipos",
            "avances",
            "accionesCorrectivas",
        ):
            rows = data_json.get(module_key, [])
            if rows in (None, ""):
                continue
            if not isinstance(rows, list):
                raise serializers.ValidationError(
                    {"dataJson": f"{module_key} debe ser una lista."},
                )
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise serializers.ValidationError(
                        {"dataJson": f"{module_key}[{index}] debe ser un objeto."},
                    )
                if not row.get("rowKey"):
                    raise serializers.ValidationError(
                        {"dataJson": f"{module_key}[{index}].rowKey es requerido."},
                    )

                if module_key == "perforacionVoladura":
                    self._validate_nested_rows(row, index, "explosivos")
                    self._validate_nested_rows(row, index, "insumos")

    def _validate_nested_rows(self, parent_row, parent_index, nested_key):
        rows = parent_row.get(nested_key, [])
        if rows in (None, ""):
            return
        if not isinstance(rows, list):
            raise serializers.ValidationError(
                {
                    "dataJson": (
                        f"perforacionVoladura[{parent_index}].{nested_key} "
                        "debe ser una lista."
                    ),
                },
            )
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise serializers.ValidationError(
                    {
                        "dataJson": (
                            f"perforacionVoladura[{parent_index}]."
                            f"{nested_key}[{index}] debe ser un objeto."
                        ),
                    },
                )
            if not row.get("rowKey"):
                raise serializers.ValidationError(
                    {
                        "dataJson": (
                            f"perforacionVoladura[{parent_index}]."
                            f"{nested_key}[{index}].rowKey es requerido."
                        ),
                    },
                )

    def _validate_sent_payload(self, data_json):
        datos_generales = data_json.get("datosGenerales", {})
        if datos_generales is not None and not isinstance(datos_generales, dict):
            raise serializers.ValidationError(
                {"dataJson": "datosGenerales debe ser un objeto."},
            )


class CartillaOperacionMinaSyncResponseSerializer(serializers.Serializer):
    clientRecordId = serializers.CharField()
    serverCartillaId = serializers.IntegerField()
    syncStatus = serializers.CharField()
    estadoWorkflow = serializers.CharField()
    created = serializers.BooleanField()
    updatedAt = serializers.DateTimeField()
    warnings = serializers.ListField(child=serializers.CharField())
