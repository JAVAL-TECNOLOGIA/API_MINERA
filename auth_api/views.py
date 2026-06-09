from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import LoginSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def module_status(request):
    return Response({"module": "auth_api", "status": "ready"})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "dni": user.dni,
                "phone": user.phone,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_view(request):
    refresh_token = request.data.get("refresh") or request.data.get("refresh_token")

    if not refresh_token:
        return Response(
            {"error": "refresh requerido"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        refresh = RefreshToken(refresh_token)
    except Exception:
        return Response(
            {"error": "refresh invalido o expirado"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response({"access_token": str(refresh.access_token)})
