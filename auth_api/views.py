from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import CurrentUserSerializer, LoginSerializer


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
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": CurrentUserSerializer(user).data,
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

    return Response({"access": str(refresh.access_token)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(CurrentUserSerializer(request.user).data)
