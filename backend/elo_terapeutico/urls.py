from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    # Autenticação
    path("auth/", include("apps.users.urls")),
    # Módulos
    path("patients/", include("apps.patients.urls")),
    path("records/", include("apps.records.urls")),
    path("agenda/", include("apps.agenda.urls")),
    path("financeiro/", include("apps.financeiro.urls")),
    path("documents/", include("apps.documents.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    # Documentação OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Health check
    path("api/health/", include("apps.users.health_urls")),
]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
