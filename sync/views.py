from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def module_status(request):
    return Response({"module": "sync", "status": "ready"})


@api_view(["GET"])
@permission_classes([AllowAny])
def mobile_bootstrap_status(request):
    return Response({"module": "mobile_bootstrap", "status": "ready"})
