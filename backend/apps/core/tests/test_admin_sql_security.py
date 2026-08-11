"""Testes de regressão e segurança do SQL Explorer administrativo."""

from __future__ import annotations

import hashlib
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError
from django.test import override_settings

from apps.audit.models import AuditLog
from apps.core.admin_sql import (
    UnsafeSQLQuery,
    _configure_postgresql_read_only,
    execute_read_only_query,
    validate_read_only_query,
)
from apps.core.models import SQLExplorerPermission
from apps.users.models import User
from config.urls import sql_explorer_urlpatterns

pytestmark = pytest.mark.django_db

SQL_EXPLORER_SETTINGS = {
    "ROOT_URLCONF": "apps.core.tests.urls_sql_explorer",
    "ADMIN_SQL_EXPLORER_ENABLED": True,
    "ADMIN_SQL_EXPLORER_DATABASE_ALIAS": "default",
    "ADMIN_SQL_EXPLORER_ALLOWED_TABLES": ["django_migrations"],
    "ADMIN_SQL_EXPLORER_MAX_ROWS": 2,
    "ADMIN_SQL_EXPLORER_TIMEOUT_MS": 1_000,
    "ADMIN_SQL_EXPLORER_PERMISSION": "core.use_sql_explorer",
}
VALID_REASON = "Verificar integridade de dados sintéticos"


def _fixture_password(label: str) -> str:
    """Monta credencial descartável sem versionar um literal com formato de segredo."""

    return "".join(("fixture", "-", label, "-", str(2026), "!"))


@pytest.fixture
def common_user() -> User:
    return User.objects.create_user(
        email="sql-common@example.test",
        full_name="Usuário comum",
        password=_fixture_password("common"),
    )


@pytest.fixture
def staff_user() -> User:
    return User.objects.create_user(
        email="sql-staff@example.test",
        full_name="Usuário staff",
        password=_fixture_password("staff"),
        is_staff=True,
    )


@pytest.fixture
def superuser() -> User:
    return User.objects.create_superuser(
        email="sql-superuser@example.test",
        full_name="Superusuário SQL",
        password=_fixture_password("superuser"),
    )


@pytest.fixture
def sql_permission() -> Permission:
    content_type = ContentType.objects.get_for_model(
        SQLExplorerPermission,
        for_concrete_model=False,
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="use_sql_explorer",
        defaults={"name": "Pode utilizar o SQL Explorer administrativo"},
    )
    return permission


@pytest.fixture
def permitted_superuser(superuser: User, sql_permission: Permission) -> User:
    superuser.user_permissions.add(sql_permission)
    return superuser


def test_feature_flag_disabled_does_not_register_sensitive_routes():
    with override_settings(ADMIN_SQL_EXPLORER_ENABLED=False):
        assert sql_explorer_urlpatterns() == []


def test_feature_flag_enabled_registers_only_expected_routes():
    with override_settings(ADMIN_SQL_EXPLORER_ENABLED=True):
        patterns = sql_explorer_urlpatterns()

    assert [pattern.name for pattern in patterns] == ["sql_explorer", "sql_schema"]


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_anonymous_user_is_denied(client):
    response = client.get("/admin/sql-explorer/")

    assert response.status_code == 403


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_common_user_is_denied(client, common_user: User):
    client.force_login(common_user)

    response = client.get("/admin/sql-explorer/")

    assert response.status_code == 403


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_staff_without_permission_is_denied(client, staff_user: User):
    client.force_login(staff_user)

    response = client.get("/admin/sql-explorer/")

    assert response.status_code == 403


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_superuser_without_explicit_permission_is_denied(client, superuser: User):
    client.force_login(superuser)

    response = client.get("/admin/sql-explorer/")

    assert response.status_code == 403


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_superuser_with_explicit_permission_can_open_tool(
    client,
    permitted_superuser: User,
):
    client.force_login(permitted_superuser)

    response = client.get("/admin/sql-explorer/")

    assert response.status_code == 200
    assert b"SQL Explorer controlado" in response.content


@pytest.mark.parametrize(
    "query",
    [
        "UPDATE users_user SET is_active = 0",
        "DELETE FROM users_user",
        "INSERT INTO users_user (email) VALUES ('blocked@example.test')",
        "DROP TABLE users_user",
    ],
)
def test_write_statements_are_rejected(query: str):
    with override_settings(ADMIN_SQL_EXPLORER_ALLOWED_TABLES=["users_user"]):
        with pytest.raises(UnsafeSQLQuery):
            validate_read_only_query(query)


@pytest.mark.parametrize(
    "query",
    [
        "WITH recent AS (SELECT 1) SELECT * FROM recent",
        "WITH deleted AS (DELETE FROM users_user RETURNING id) SELECT * FROM deleted",
    ],
)
def test_ctes_are_rejected(query: str):
    with override_settings(ADMIN_SQL_EXPLORER_ALLOWED_TABLES=["users_user"]):
        with pytest.raises(UnsafeSQLQuery):
            validate_read_only_query(query)


def test_multiple_statements_are_rejected():
    with pytest.raises(UnsafeSQLQuery):
        validate_read_only_query("SELECT 1; SELECT 2;")


@pytest.mark.parametrize(
    "query",
    [
        "EXPLAIN SELECT 1",
        "EXPLAIN ANALYZE SELECT 1",
    ],
)
def test_explain_is_rejected(query: str):
    with pytest.raises(UnsafeSQLQuery):
        validate_read_only_query(query)


def test_subquery_is_rejected():
    with override_settings(ADMIN_SQL_EXPLORER_ALLOWED_TABLES=["django_migrations"]):
        with pytest.raises(UnsafeSQLQuery):
            validate_read_only_query(
                "SELECT * FROM (SELECT * FROM django_migrations) AS nested"
            )


def test_query_referencing_table_outside_allowlist_is_rejected():
    with override_settings(ADMIN_SQL_EXPLORER_ALLOWED_TABLES=["django_migrations"]):
        with pytest.raises(UnsafeSQLQuery, match="tabela não autorizada"):
            validate_read_only_query("SELECT id FROM users_user")


def test_allowed_select_exposes_only_validated_table_names():
    with override_settings(ADMIN_SQL_EXPLORER_ALLOWED_TABLES=["django_migrations"]):
        validated = validate_read_only_query(
            "SELECT id, app, name FROM django_migrations ORDER BY id DESC"
        )

    assert validated.referenced_tables == frozenset({"django_migrations"})


@override_settings(
    ADMIN_SQL_EXPLORER_DATABASE_ALIAS="default",
    ADMIN_SQL_EXPLORER_MAX_ROWS=2,
    ADMIN_SQL_EXPLORER_TIMEOUT_MS=1_000,
)
def test_query_result_is_limited_and_marked_as_truncated():
    columns, rows, truncated = execute_read_only_query(
        "SELECT 1 AS value UNION ALL SELECT 2 UNION ALL SELECT 3"
    )

    assert columns == ["value"]
    assert rows == [(1,), (2,)]
    assert truncated is True


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_justification_is_required_before_execution(
    client,
    permitted_superuser: User,
):
    client.force_login(permitted_superuser)

    response = client.post(
        "/admin/sql-explorer/",
        {"sql": "SELECT 1", "reason": "curta"},
    )

    assert response.status_code == 400
    assert b"pelo menos 12 caracteres" in response.content
    assert AuditLog.objects.count() == 0


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_database_error_is_sanitized_and_does_not_leak_internal_details(
    client,
    permitted_superuser: User,
):
    client.force_login(permitted_superuser)
    internal_detail = "relation clinical_secret_table does not exist"

    with patch(
        "apps.core.admin_sql.execute_read_only_query",
        side_effect=DatabaseError(internal_detail),
    ):
        response = client.post(
            "/admin/sql-explorer/",
            {"sql": "SELECT 1", "reason": VALID_REASON},
        )

    assert response.status_code == 503
    assert internal_detail.encode() not in response.content
    assert b"limites de seguran" in response.content


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_audit_stores_query_hash_but_never_the_full_query(
    client,
    permitted_superuser: User,
):
    client.force_login(permitted_superuser)
    query = "SELECT id FROM django_migrations ORDER BY id DESC"

    response = client.post(
        "/admin/sql-explorer/",
        {"sql": query, "reason": VALID_REASON},
    )

    assert response.status_code == 200
    entry = AuditLog.objects.get(user=permitted_superuser)
    expected_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    assert expected_hash in entry.object_repr
    assert VALID_REASON in entry.object_repr
    assert query not in entry.object_repr


@override_settings(**SQL_EXPLORER_SETTINGS)
def test_schema_endpoint_returns_only_allowlisted_tables(
    client,
    permitted_superuser: User,
):
    client.force_login(permitted_superuser)

    response = client.get("/admin/sql-schema/")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["schema"]) <= {"django_migrations"}
    assert "users_user" not in payload["schema"]


def test_postgresql_defense_sets_read_only_transaction_and_timeout():
    class CursorSpy:
        def __init__(self):
            self.calls: list[tuple[str, object]] = []

        def execute(self, sql: str, params=None):
            self.calls.append((sql, params))

    cursor = CursorSpy()

    _configure_postgresql_read_only(cursor, 1_500)

    assert cursor.calls == [
        ("SET LOCAL TRANSACTION READ ONLY", None),
        (
            "SELECT set_config('statement_timeout', %s, true)",
            ["1500ms"],
        ),
    ]
