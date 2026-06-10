from django.urls import path

from .views import cartilla_attachments, delete_attachment, module_status


urlpatterns = [
    path("", module_status, name="attachments_status"),
    path(
        "cartillas/<int:cartilla_id>/",
        cartilla_attachments,
        name="cartilla_attachments",
    ),
    path(
        "<int:attachment_id>/",
        delete_attachment,
        name="delete_attachment",
    ),
]
