from django.urls import path

from .views import (
    cartilla_approve,
    cartilla_by_client_record,
    cartilla_close,
    cartilla_detail,
    cartilla_list,
    cartilla_observe,
    cartilla_reject,
    cartilla_render_data,
    cartilla_submit,
    cartilla_summary,
    module_status,
)


urlpatterns = [
    path("", module_status, name="mina_status"),
    path("cartillas/", cartilla_list, name="mina_cartilla_list"),
    path("cartillas/<int:cartilla_id>/", cartilla_detail, name="mina_cartilla_detail"),
    path("cartillas/<int:cartilla_id>/summary/", cartilla_summary, name="mina_cartilla_summary"),
    path(
        "cartillas/<int:cartilla_id>/render-data/",
        cartilla_render_data,
        name="mina_cartilla_render_data",
    ),
    path("cartillas/<int:cartilla_id>/submit/", cartilla_submit, name="mina_cartilla_submit"),
    path("cartillas/<int:cartilla_id>/observe/", cartilla_observe, name="mina_cartilla_observe"),
    path("cartillas/<int:cartilla_id>/approve/", cartilla_approve, name="mina_cartilla_approve"),
    path("cartillas/<int:cartilla_id>/reject/", cartilla_reject, name="mina_cartilla_reject"),
    path("cartillas/<int:cartilla_id>/close/", cartilla_close, name="mina_cartilla_close"),
    path(
        "cartillas/by-client-record/<str:client_record_id>/",
        cartilla_by_client_record,
        name="mina_cartilla_by_client_record",
    ),
]
