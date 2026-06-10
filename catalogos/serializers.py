from rest_framework import serializers

from .models import (
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
    Trabajador,
    Turno,
    UnidadMedida,
    Zona,
)


class CatalogoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "codigo",
            "nombre",
            "descripcion",
            "is_active",
            "updated_at",
        )


class AreaSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = Area


class GuardiaSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = Guardia


class ClimaSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = Clima


class CargoSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = Cargo


class ProductoSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = Producto


class UnidadMedidaSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = UnidadMedida


class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields = (
            "id",
            "codigo",
            "nombre",
            "hora_inicio",
            "hora_fin",
            "cruza_medianoche",
            "is_active",
            "updated_at",
        )


class EmpresaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="razon_social", read_only=True)

    class Meta:
        model = Empresa
        fields = (
            "id",
            "codigo",
            "ruc",
            "nombre",
            "razon_social",
            "descripcion",
            "is_active",
            "updated_at",
        )


class TrabajadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trabajador
        fields = (
            "id",
            "codigo",
            "dni",
            "nombres",
            "apellidos",
            "cargo_id",
            "empresa_id",
            "telefono",
            "email",
            "es_ingeniero_minero",
            "es_supervisor",
            "es_operador",
            "is_active",
            "updated_at",
        )


class ZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zona
        fields = (
            "id",
            "codigo",
            "letra",
            "nombre",
            "descripcion",
            "is_active",
            "updated_at",
        )


class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nivel
        fields = (
            "id",
            "codigo",
            "numero",
            "descripcion",
            "is_active",
            "updated_at",
        )


class LaborSerializer(serializers.ModelSerializer):
    class Meta:
        model = Labor
        fields = (
            "id",
            "codigo",
            "titulo",
            "descripcion",
            "zona_id",
            "nivel_id",
            "is_active",
            "updated_at",
        )


class LaborFrenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LaborFrente
        fields = (
            "id",
            "codigo",
            "titulo",
            "descripcion",
            "labor_id",
            "zona_id",
            "nivel_id",
            "is_active",
            "updated_at",
        )


class GrupoPerforacionSerializer(CatalogoBaseSerializer):
    class Meta(CatalogoBaseSerializer.Meta):
        model = GrupoPerforacion


class GrupoPerforacionIntegranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoPerforacionIntegrante
        fields = (
            "id",
            "grupo_id",
            "trabajador_id",
            "rol_en_grupo",
            "is_active",
            "updated_at",
        )


class ExplosivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Explosivo
        fields = (
            "id",
            "codigo",
            "nombre",
            "unidad_medida_id",
            "descripcion",
            "is_active",
            "updated_at",
        )


class InsumoAccesorioSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsumoAccesorio
        fields = (
            "id",
            "codigo",
            "nombre",
            "unidad_medida_id",
            "descripcion",
            "is_active",
            "updated_at",
        )


class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = (
            "id",
            "codigo",
            "nombre",
            "tipo",
            "empresa_id",
            "descripcion",
            "is_active",
            "updated_at",
        )
