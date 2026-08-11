"""Regras arquiteturais dedicadas ao domínio audit."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
AUDIT = BACKEND / "apps" / "audit"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _validate_required_paths(errors: list[str]) -> None:
    required = [
        AUDIT / "README.md",
        AUDIT / "apps.py",
        AUDIT / "admin" / "audit_logs.py",
        AUDIT / "exceptions" / "domain.py",
        AUDIT / "integrations" / "drf.py",
        AUDIT / "integrations" / "django_admin.py",
        AUDIT / "models" / "audit_logs.py",
        AUDIT / "models" / "querysets.py",
        AUDIT / "selectors" / "audit_logs.py",
        AUDIT / "services" / "events.py",
        AUDIT / "services" / "request_context.py",
        AUDIT / "services" / "sanitization.py",
        AUDIT / "types" / "events.py",
        AUDIT / "tests" / "architecture" / "test_audit_architecture.py",
        AUDIT / "migrations" / "0001_initial.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Estrutura obrigatória de audit ausente: {_relative(path)}")


def _validate_app_config(errors: list[str]) -> None:
    source = (AUDIT / "apps.py").read_text(encoding="utf-8")
    if 'name = "apps.audit"' not in source:
        errors.append("AuditConfig não usa o pacote apps.audit")
    if 'label = "audit"' not in source:
        errors.append("AuditConfig não declara explicitamente o app label audit")
    settings = (BACKEND / "config" / "settings" / "base.py").read_text(encoding="utf-8")
    if '"apps.audit.apps.AuditConfig"' not in settings:
        errors.append("AuditConfig não está registrado explicitamente no INSTALLED_APPS")


def _validate_root(errors: list[str]) -> None:
    root_files = {path.name for path in AUDIT.iterdir() if path.is_file()}
    allowed = {"README.md", "__init__.py", "apps.py"}
    if root_files != allowed:
        errors.append(
            f"Raiz de audit deve conter apenas {sorted(allowed)}; encontrado {sorted(root_files)}"
        )


def _validate_historical_contract(errors: list[str]) -> None:
    model_source = (AUDIT / "models" / "audit_logs.py").read_text(encoding="utf-8")
    if 'db_table = "users_auditlog"' not in model_source:
        errors.append("AuditLog não preserva a tabela histórica users_auditlog")
    if "audit_auditlog" in model_source:
        errors.append("AuditLog referencia a tabela proibida audit_auditlog")
    migration = (AUDIT / "migrations" / "0001_initial.py").read_text(encoding="utf-8")
    if "SeparateDatabaseAndState" not in migration or "users_auditlog" not in migration:
        errors.append("Migration histórica de audit perdeu SeparateDatabaseAndState/users_auditlog")


def _validate_public_writes(errors: list[str]) -> None:
    direct_create = re.compile(r"\bAuditLog\.objects\.create\s*\(")
    direct_constructor = re.compile(r"(?<!class\s)\bAuditLog\s*\(")
    allowed_parts = {
        str(AUDIT / "services" / "events.py"),
    }
    for path in BACKEND.rglob("*.py"):
        if "migrations" in path.parts or "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if str(path) not in allowed_parts and (
            direct_create.search(source) or direct_constructor.search(source)
        ):
            errors.append(f"Escrita direta de AuditLog fora do service: {_relative(path)}")


def _validate_legacy_imports(errors: list[str]) -> None:
    patterns = (
        "apps.audit.services.access_logging",
        "from core.audit",
        "from apps.core.audit",
        "import core.audit",
        "import apps.core.audit",
    )
    rule_file = Path(__file__).resolve()
    for path in BACKEND.rglob("*.py"):
        if "migrations" in path.parts or path.resolve() == rule_file:
            continue
        source = path.read_text(encoding="utf-8")
        if any(pattern in source for pattern in patterns):
            errors.append(f"Import legado de auditoria: {_relative(path)}")


def _validate_admin(errors: list[str]) -> None:
    source = (AUDIT / "integrations" / "django_admin.py").read_text(encoding="utf-8")
    required = (
        "def has_add_permission",
        "def has_change_permission",
        "def has_delete_permission",
        "return False",
    )
    if any(token not in source for token in required):
        errors.append("Admin de audit não está explicitamente read-only")


def _validate_exports(errors: list[str]) -> None:
    public_inits = [
        AUDIT / "admin" / "__init__.py",
        AUDIT / "exceptions" / "__init__.py",
        AUDIT / "integrations" / "__init__.py",
        AUDIT / "models" / "__init__.py",
        AUDIT / "selectors" / "__init__.py",
        AUDIT / "services" / "__init__.py",
        AUDIT / "types" / "__init__.py",
    ]
    for path in public_inits:
        source = path.read_text(encoding="utf-8")
        if "import *" in source:
            errors.append(f"Export público usa import curinga: {_relative(path)}")
        if "__all__" not in source:
            errors.append(f"Export público sem __all__ explícito: {_relative(path)}")


def validate_audit_architecture(errors: list[str]) -> None:
    _validate_required_paths(errors)
    _validate_app_config(errors)
    _validate_root(errors)
    _validate_historical_contract(errors)
    _validate_public_writes(errors)
    _validate_legacy_imports(errors)
    _validate_admin(errors)
    _validate_exports(errors)
