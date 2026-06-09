from django.urls import path

from .views import module_status


urlpatterns = [
    path("", module_status, name="cartillas_status"),
]
