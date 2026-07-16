"""URLConf isolado para testar o SQL Explorer com a feature flag ativa."""

from django.contrib import admin
from django.urls import path

from apps.core.admin_sql import sql_explorer_view, sql_schema_view

urlpatterns = [
    path("admin/sql-explorer/", sql_explorer_view, name="sql_explorer"),
    path("admin/sql-schema/", sql_schema_view, name="sql_schema"),
    path("admin/", admin.site.urls),
]
