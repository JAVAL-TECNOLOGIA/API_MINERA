from django.urls import path

from .views import login_view, module_status, refresh_view


urlpatterns = [
    path("", module_status, name="auth_api_status"),
    path("login/", login_view, name="auth_api_login"),
    path("refresh/", refresh_view, name="auth_api_refresh"),
]
