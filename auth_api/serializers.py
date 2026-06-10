from django.contrib.auth import authenticate
from rest_framework import serializers


def get_user_roles(user):
    roles = list(
        user.mina_profiles.filter(
            is_active=True,
            deleted_at__isnull=True,
            role__is_active=True,
            role__deleted_at__isnull=True,
        )
        .select_related("role")
        .values_list("role__code", flat=True)
    )

    if user.is_superuser and "admin" not in roles:
        roles.append("admin")

    return roles


class CurrentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True, allow_blank=True)
    first_name = serializers.CharField(read_only=True, allow_blank=True)
    last_name = serializers.CharField(read_only=True, allow_blank=True)
    dni = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    phone = serializers.CharField(read_only=True, allow_blank=True)
    is_superuser = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    roles = serializers.SerializerMethodField()

    def get_roles(self, obj):
        return get_user_roles(obj)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Credenciales invalidas")
        if not user.is_active:
            raise serializers.ValidationError("Usuario inactivo")

        attrs["user"] = user
        return attrs
