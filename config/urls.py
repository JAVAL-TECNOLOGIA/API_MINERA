from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("auth_api.urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/mobile/", include("sync.mobile_urls")),
    path("api/sync/", include("sync.urls")),
    path("api/catalogos/", include("catalogos.urls")),
    path("api/cartillas/", include("cartillas.urls")),
    path("api/mina/", include("mina.urls")),
    path("api/attachments/", include("attachments.urls")),
    path("api/reports/", include("reports.urls")),
    # Legacy Don Luis API kept temporarily while the new backend is built.
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
