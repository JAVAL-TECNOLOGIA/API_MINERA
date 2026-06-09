from django.urls import path

from .views import mobile_bootstrap_status


urlpatterns = [
    path("bootstrap/", mobile_bootstrap_status, name="mobile_bootstrap_status"),
]
