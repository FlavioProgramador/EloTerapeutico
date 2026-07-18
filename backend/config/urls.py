from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.billing.api.legacy.routes import legacy_billing_route_enabled

api_v1_patterns = [
    path("auth/", include("apps.users.urls")),
    path("patients/", include("apps.patients.urls")),
    path("records/", include("apps.records.urls")),
    path("scheduling/", include("apps.scheduling.api.v1.urls")),
    path("agenda/", include("apps.scheduling.api.legacy.urls")),
    path("financeiro/", include("apps.financeiro.urls")),
    path("documents/", include("apps.documents.api.v1.urls")),
    path("reports/", include("apps.reports.urls")),
    path("forms/", include("apps.forms.urls")),
    path("billing/", include("apps.billing.api.v1.urls")),
    path("communications/", include("apps.communications.urls")),
    path("public/communications/", include("apps.communications.urls_public")),
]


def sql_explorer_urlpatterns():
    """Registra as rotas sensíveis somente com a feature flag ativa."""

    if not getattr(settings, "ADMIN_SQL_EXPLORER_ENABLED", False):
        return []

    from apps.core.admin_sql import sql_explorer_view, sql_schema_view

    return [
        path("admin/sql-explorer/", sql_explorer_view, name="sql_explorer"),
        path("admin/sql-schema/", sql_schema_view, name="sql_schema"),
    ]


urlpatterns = [
    *sql_explorer_urlpatterns(),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/health/", include("apps.users.health_urls")),
    path("health/", include("apps.core.api.urls")),
]

if legacy_billing_route_enabled():
    urlpatterns.append(
        path("api/billing/", include("apps.billing.api.legacy.urls"))
    )

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
