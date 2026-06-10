from django.urls import path

from .views import TipoCartillaListView


urlpatterns = [
    path("tipos/", TipoCartillaListView.as_view(), name="cartillas_tipos"),
]
