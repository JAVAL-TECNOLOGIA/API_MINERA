from django.urls import path

from .views import mobile_bootstrap


urlpatterns = [
    path("bootstrap/", mobile_bootstrap, name="mobile_bootstrap"),
]
