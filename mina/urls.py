from django.urls import path

from .views import (
    cartilla_by_client_record,
    cartilla_detail,
    cartilla_list,
    module_status,
)


urlpatterns = [
    path("", module_status, name="mina_status"),
    path("cartillas/", cartilla_list, name="mina_cartilla_list"),
    path("cartillas/<int:cartilla_id>/", cartilla_detail, name="mina_cartilla_detail"),
    path(
        "cartillas/by-client-record/<str:client_record_id>/",
        cartilla_by_client_record,
        name="mina_cartilla_by_client_record",
    ),
]
