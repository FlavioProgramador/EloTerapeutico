"""SQL Explorer administrativo com defesa em profundidade.

A ferramenta permanece desabilitada por padrão e não é registrada em produção.
Quando habilitada em ambiente autorizado, somente consultas ``SELECT`` simples
sobre tabelas explicitamente permitidas podem ser executadas. A validação
estrutural é combinada com transação read-only no PostgreSQL, timeout, limite de
linhas e auditoria por hash.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any

import sqlparse
from django.conf import settings
from django.contrib import admin
from django.db import DatabaseError, connections, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from sqlparse.sql import Identifier, IdentifierList, Parenthesis, Statement
from sqlparse.tokens import DDL, DML, Comment, Keyword

from apps.audit.models import AuditLog
from apps.audit.services import log_access

logger = logging.getLogger(__name__)

DEFAULT_PERMISSION = "core.use_sql_explorer"
DEFAULT_MAX_ROWS = 100
DEFAULT_TIMEOUT_MS = 2_000
MAX_QUERY_LENGTH = 20_000
MIN_REASON_LENGTH = 12
MAX_REASON_LENGTH = 160

_FROM_OR_JOIN_KEYWORDS = {
    "FROM",
    "JOIN",
    "LEFT JOIN",
    "RIGHT JOIN",
    "INNER JOIN",
    "FULL JOIN",
    "FULL OUTER JOIN",
    "CROSS JOIN",
}
_BLOCKED_KEYWORDS = {
    "ALTER",
    "ANALYZE",
    "CALL",
    "CLUSTER",
    "COMMENT",
    "COPY",
    "CREATE",
    "DELETE",
    "DO",
    "DROP",
    "EXECUTE",
    "EXPLAIN",
    "GRANT",
    "INSERT",
    "LOCK",
    "MERGE",
    "PRAGMA",
    "REFRESH",
    "REINDEX",
    "REVOKE",
    "SET",
    "SHOW",
    "TRUNCATE",
    "UPDATE",
    "VACUUM",
    "WITH",
}
_BLOCKED_FUNCTIONS = {
    "DBLINK",
    "LO_EXPORT",
    "LO_IMPORT",
    "PG_ADVISORY_LOCK",
    "PG_READ_BINARY_FILE",
    "PG_READ_FILE",
    "PG_SLEEP",
    "PG_TERMINATE_BACKEND",
    "PG_TRY_ADVISORY_LOCK",
    "SET_CONFIG",
}


class UnsafeSQLQuery(ValueError):
    """Consulta rejeitada antes de chegar ao banco de dados."""


@dataclass(frozen=True)
class ValidatedSQLQuery:
    """Resultado mínimo da validação estrutural da consulta."""

    statement: Statement
    referenced_tables: frozenset[str]


def _setting_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(getattr(settings, name, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8", errors="replace")).hexdigest()


def _clean_reason(reason: str) -> str:
    return " ".join(str(reason or "").split())[:MAX_REASON_LENGTH]


def _token_matches(token: Any, token_type: Any) -> bool:
    return token.ttype is not None and token.ttype in token_type


def _allowed_tables() -> frozenset[str]:
    configured = getattr(settings, "ADMIN_SQL_EXPLORER_ALLOWED_TABLES", [])
    return frozenset(
        str(table).strip().strip('"').lower()
        for table in configured
        if str(table).strip()
    )


def _permission_parts() -> tuple[str, str]:
    configured = str(getattr(settings, "ADMIN_SQL_EXPLORER_PERMISSION", DEFAULT_PERMISSION))
    if "." not in configured:
        app_label, codename = DEFAULT_PERMISSION.split(".", 1)
        return app_label, codename
    app_label, codename = configured.split(".", 1)
    return app_label, codename


def _has_explicit_permission(user: Any) -> bool:
    """Exige uma atribuição real, sem o bypass automático de superusuário."""

    app_label, codename = _permission_parts()
    direct_lookup = {
        "content_type__app_label": app_label,
        "codename": codename,
    }
    group_lookup = {
        "permissions__content_type__app_label": app_label,
        "permissions__codename": codename,
    }
    return user.user_permissions.filter(**direct_lookup).exists() or user.groups.filter(
        **group_lookup
    ).exists()


def can_use_sql_explorer(user: Any) -> bool:
    return bool(
        getattr(settings, "ADMIN_SQL_EXPLORER_ENABLED", False)
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_superuser", False)
        and _has_explicit_permission(user)
    )


def sql_explorer_access_required(view_func):
    """Bloqueia acesso sem revelar detalhes de configuração ou permissão."""

    @wraps(view_func)
    def wrapped(request: HttpRequest, *args, **kwargs):
        if not getattr(settings, "ADMIN_SQL_EXPLORER_ENABLED", False):
            return HttpResponse(status=404)
        if not can_use_sql_explorer(request.user):
            if getattr(request.user, "is_authenticated", False):
                log_access(
                    request,
                    AuditLog.Action.VIEW,
                    obj_repr="SQL Explorer | status=acesso_negado",
                )
            return HttpResponseForbidden("Acesso negado.")
        return view_func(request, *args, **kwargs)

    return wrapped


def _first_significant_token(statement: Statement):
    for token in statement.tokens:
        if token.is_whitespace or _token_matches(token, Comment):
            continue
        return token
    return None


def _normalize_identifier(identifier: Identifier) -> str:
    if any(isinstance(token, Parenthesis) for token in identifier.tokens):
        raise UnsafeSQLQuery("Subconsultas e funções na cláusula FROM não são permitidas.")

    real_name = identifier.get_real_name()
    if not real_name:
        raise UnsafeSQLQuery("Não foi possível validar uma tabela referenciada.")

    parent_name = identifier.get_parent_name()
    if parent_name:
        return f"{parent_name}.{real_name}".strip('"').lower()
    return str(real_name).strip('"').lower()


def _extract_referenced_tables(statement: Statement) -> frozenset[str]:
    """Extrai tabelas de SELECTs simples e falha fechado em estruturas ambíguas."""

    referenced: set[str] = set()
    expecting_table = False

    for token in statement.tokens:
        if token.is_whitespace or _token_matches(token, Comment):
            continue

        if isinstance(token, Parenthesis) and "SELECT" in token.value.upper():
            raise UnsafeSQLQuery("Subconsultas não são permitidas no SQL Explorer.")

        normalized = (
            token.normalized.upper() if hasattr(token, "normalized") else token.value.upper()
        )
        if _token_matches(token, Keyword) and normalized in _FROM_OR_JOIN_KEYWORDS:
            expecting_table = True
            continue

        if not expecting_table:
            continue

        if isinstance(token, IdentifierList):
            identifiers = list(token.get_identifiers())
            if not identifiers:
                raise UnsafeSQLQuery("Não foi possível validar as tabelas da consulta.")
            for identifier in identifiers:
                referenced.add(_normalize_identifier(identifier))
        elif isinstance(token, Identifier):
            referenced.add(_normalize_identifier(token))
        else:
            raise UnsafeSQLQuery(
                "Somente tabelas explícitas são permitidas após FROM ou JOIN."
            )

        expecting_table = False

    if expecting_table:
        raise UnsafeSQLQuery("A consulta possui uma cláusula FROM ou JOIN incompleta.")

    return frozenset(referenced)


def validate_read_only_query(query: str) -> ValidatedSQLQuery:
    """Valida uma consulta sem depender somente da primeira palavra."""

    if not query or not query.strip():
        raise UnsafeSQLQuery("Informe uma consulta SELECT.")
    if len(query) > MAX_QUERY_LENGTH:
        raise UnsafeSQLQuery("A consulta excede o tamanho máximo permitido.")

    statements = [statement for statement in sqlparse.parse(query) if str(statement).strip()]
    split_statements = [statement for statement in sqlparse.split(query) if statement.strip()]
    if len(statements) != 1 or len(split_statements) != 1:
        raise UnsafeSQLQuery("Apenas uma instrução SQL é permitida por execução.")

    statement = statements[0]
    first_token = _first_significant_token(statement)
    if first_token is None:
        raise UnsafeSQLQuery("Informe uma consulta SELECT.")

    first_keyword = first_token.normalized.upper()
    if first_keyword.startswith("WITH"):
        raise UnsafeSQLQuery("CTEs não são permitidas no SQL Explorer.")
    if statement.get_type().upper() != "SELECT":
        raise UnsafeSQLQuery("Somente consultas SELECT são permitidas.")

    for token in statement.flatten():
        normalized = token.normalized.upper()
        if _token_matches(token, DDL):
            raise UnsafeSQLQuery("Comandos de definição de dados não são permitidos.")
        if _token_matches(token, DML) and normalized != "SELECT":
            raise UnsafeSQLQuery("Comandos de alteração de dados não são permitidos.")
        if normalized in _BLOCKED_KEYWORDS:
            raise UnsafeSQLQuery(f"O comando {normalized} não é permitido.")
        if normalized in _BLOCKED_FUNCTIONS:
            raise UnsafeSQLQuery("A consulta utiliza uma função não permitida.")

    referenced_tables = _extract_referenced_tables(statement)
    allowed_tables = _allowed_tables()
    unauthorized_tables = referenced_tables - allowed_tables
    if unauthorized_tables:
        raise UnsafeSQLQuery(
            "A consulta referencia uma tabela não autorizada para inspeção."
        )

    return ValidatedSQLQuery(
        statement=statement,
        referenced_tables=referenced_tables,
    )


def _configure_postgresql_read_only(cursor, timeout_ms: int) -> None:
    """Aplica defesa no próprio PostgreSQL, além da validação de aplicação."""

    cursor.execute("SET LOCAL TRANSACTION READ ONLY")
    cursor.execute(
        "SELECT set_config('statement_timeout', %s, true)",
        [f"{timeout_ms}ms"],
    )


def execute_read_only_query(
    query: str,
) -> tuple[list[str], list[tuple[Any, ...]], bool]:
    database_alias = str(
        getattr(settings, "ADMIN_SQL_EXPLORER_DATABASE_ALIAS", "default")
    )
    max_rows = _setting_int(
        "ADMIN_SQL_EXPLORER_MAX_ROWS",
        DEFAULT_MAX_ROWS,
        minimum=1,
        maximum=500,
    )
    timeout_ms = _setting_int(
        "ADMIN_SQL_EXPLORER_TIMEOUT_MS",
        DEFAULT_TIMEOUT_MS,
        minimum=100,
        maximum=10_000,
    )
    database = connections[database_alias]

    with transaction.atomic(using=database_alias):
        with database.cursor() as cursor:
            if database.vendor == "postgresql":
                _configure_postgresql_read_only(cursor, timeout_ms)

            cursor.execute(query)
            if cursor.description is None:
                raise UnsafeSQLQuery(
                    "A consulta não retornou um conjunto de leitura."
                )

            columns = [column[0] for column in cursor.description]
            fetched = list(cursor.fetchmany(max_rows + 1))
            truncated = len(fetched) > max_rows
            rows = fetched[:max_rows]

        transaction.set_rollback(True, using=database_alias)

    return columns, rows, truncated


def _audit_query(
    request: HttpRequest,
    *,
    query: str,
    reason: str,
    status: str,
) -> None:
    digest = _query_hash(query)
    safe_reason = _clean_reason(reason)
    log_access(
        request,
        AuditLog.Action.VIEW,
        obj_repr=(
            f"SQL Explorer | status={status} | hash={digest} | motivo={safe_reason}"
        ),
    )


@sql_explorer_access_required
@require_http_methods(["GET", "POST"])
def sql_explorer_view(request: HttpRequest) -> HttpResponse:
    """Executa SELECTs controlados em ambiente explicitamente autorizado."""

    context = admin.site.each_context(request)
    context.update(
        {
            "title": "SQL Explorer",
            "allowed_tables": sorted(_allowed_tables()),
            "max_rows": _setting_int(
                "ADMIN_SQL_EXPLORER_MAX_ROWS",
                DEFAULT_MAX_ROWS,
                minimum=1,
                maximum=500,
            ),
            "timeout_ms": _setting_int(
                "ADMIN_SQL_EXPLORER_TIMEOUT_MS",
                DEFAULT_TIMEOUT_MS,
                minimum=100,
                maximum=10_000,
            ),
        }
    )

    query = request.POST.get("sql", "").strip()
    reason = _clean_reason(request.POST.get("reason", ""))
    context["query"] = query
    context["reason"] = reason

    if request.method != "POST":
        return render(request, "admin/sql_explorer.html", context)

    if len(reason) < MIN_REASON_LENGTH:
        context["error"] = (
            f"Informe uma justificativa com pelo menos {MIN_REASON_LENGTH} caracteres."
        )
        return render(request, "admin/sql_explorer.html", context, status=400)

    try:
        validate_read_only_query(query)
        columns, rows, truncated = execute_read_only_query(query)
    except UnsafeSQLQuery as exc:
        _audit_query(request, query=query, reason=reason, status="bloqueada")
        context["error"] = str(exc)
        return render(request, "admin/sql_explorer.html", context, status=400)
    except DatabaseError as exc:
        digest = _query_hash(query)
        logger.warning(
            "admin_sql_query_failed",
            extra={
                "query_hash": digest,
                "exception_type": exc.__class__.__name__,
            },
        )
        _audit_query(request, query=query, reason=reason, status="erro_banco")
        context["error"] = (
            "A consulta não pôde ser concluída dentro dos limites de segurança."
        )
        return render(request, "admin/sql_explorer.html", context, status=503)
    except Exception as exc:
        digest = _query_hash(query)
        logger.error(
            "admin_sql_unexpected_failure",
            extra={
                "query_hash": digest,
                "exception_type": exc.__class__.__name__,
            },
        )
        _audit_query(request, query=query, reason=reason, status="erro_interno")
        context["error"] = "Não foi possível executar a consulta com segurança."
        return render(request, "admin/sql_explorer.html", context, status=500)

    _audit_query(request, query=query, reason=reason, status="concluida")
    logger.info(
        "admin_sql_query_completed",
        extra={
            "query_hash": _query_hash(query),
            "row_count": len(rows),
            "truncated": truncated,
            "user_id": request.user.pk,
        },
    )
    context.update(
        {
            "columns": columns,
            "rows": rows,
            "truncated": truncated,
        }
    )
    return render(request, "admin/sql_explorer.html", context)


@sql_explorer_access_required
@require_GET
def sql_schema_view(request: HttpRequest) -> JsonResponse:
    """Retorna somente o schema das tabelas explicitamente autorizadas."""

    database_alias = str(
        getattr(settings, "ADMIN_SQL_EXPLORER_DATABASE_ALIAS", "default")
    )
    allowed_tables = _allowed_tables()
    schema: dict[str, list[str]] = {}

    try:
        database = connections[database_alias]
        with database.cursor() as cursor:
            existing_tables = set(database.introspection.table_names(cursor))
            for table in sorted(existing_tables & allowed_tables):
                columns = database.introspection.get_table_description(cursor, table)
                schema[table] = [column.name for column in columns]
    except Exception as exc:
        logger.error(
            "admin_sql_schema_failed",
            extra={"exception_type": exc.__class__.__name__},
        )
        return JsonResponse({"error": "Schema indisponível."}, status=503)

    return JsonResponse({"schema": schema})
