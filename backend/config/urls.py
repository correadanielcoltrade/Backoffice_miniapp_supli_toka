"""URLs raiz del proyecto. Todas las APIs cuelgan de /api/."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import CustomTokenObtainPairView

api_patterns = [
    # Autenticacion JWT
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Modulos
    path("", include("apps.users.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.inventory.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.ads.urls")),
    path("", include("apps.reverse_logistics.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.toka.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    # API publica para consumidores externos (API Key, versionada)
    path("api/public/v1/", include("apps.public_api.urls")),
    # BFF que consume la mini-app de Wigilabs/Supli (rutas /v1/... tal cual la spec)
    path("v1/", include("apps.miniapp.urls")),
    # Documentacion OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
