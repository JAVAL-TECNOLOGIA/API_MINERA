from rest_framework import serializers

from .models import TipoCartilla


class TipoCartillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoCartilla
        fields = (
            "id",
            "codigo",
            "nombre",
            "descripcion",
            "version",
            "schema_json",
            "is_active",
            "updated_at",
        )
