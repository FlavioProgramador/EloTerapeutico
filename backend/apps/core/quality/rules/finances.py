"""Regras arquiteturais dedicadas ao domínio finances."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
FINANCES = BACKEND / "apps" / "finances"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _validate_required_paths(errors: list[str]) -> None:
    required = [
        FINANCES / "README.md", FINANCES / "apps.py",
        FINANCES / "admin" / "financial_transactions.py",
        FINANCES / "admin" / "monthly_subscriptions.py",
        FINANCES / "api" / "v1" / "urls.py",
        FINANCES / "api" / "v1" / "filters" / "financial_transactions.py",
        FINANCES / "api" / "v1" / "permissions" / "finances.py",
        FINANCES / "api" / "v1" / "serializers" / "financial_transactions.py",
        FINANCES / "api" / "v1" / "serializers" / "monthly_subscriptions.py",
        FINANCES / "api" / "v1" / "views" / "financial_transactions.py",
        FINANCES / "exceptions" / "domain.py",
        FINANCES / "integrations" / "scheduling.py",
        FINANCES / "models" / "financial_transactions.py",
        FINANCES / "models" / "monthly_subscriptions.py",
        FINANCES / "selectors" / "summaries.py",
        FINANCES / "services" / "payments.py",
        FINANCES / "services" / "appointment_charges.py",
        FINANCES / "tests" / "architecture" / "test_finances_refactor.py",
        FINANCES / "migrations" / "0001_initial.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Estrutura obrigatória de finances ausente: {_relative(path)}")


def _validate_app_config(errors: list[str]) -> None:
    source = (FINANCES / "apps.py").read_text(encoding="utf-8")
    if 'name = "apps.finances"' not in source:
        errors.append("FinancesConfig não usa o pacote apps.finances")
    if 'label = "financeiro"' not in source:
        errors.append("FinancesConfig não preserva o app label financeiro")


def _validate_root(errors: list[str]) -> None:
    root_files = {path.name for path in FINANCES.iterdir() if path.is_file()}
    allowed = {"README.md", "__init__.py", "apps.py"}
    if root_files != allowed:
        errors.append(
            f"Raiz de finances deve conter apenas {sorted(allowed)}; encontrado {sorted(root_files)}"
        )


def _validate_removed_legacy(errors: list[str]) -> None:
    if (BACKEND / "apps" / "financeiro").exists():
        errors.append("O pacote legado backend/apps/financeiro deve permanecer removido")
    pattern = re.compile(r"(?m)^\s*(?:from\s+apps\.financeiro\b|import\s+apps\.financeiro\b)")
    for path in BACKEND.rglob("*.py"):
        if "migrations" in path.parts:
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            errors.append(f"Import do pacote removido apps.financeiro: {_relative(path)}")


def _validate_routes(errors: list[str]) -> None:
    source = (BACKEND / "config" / "urls.py").read_text(encoding="utf-8")
    if 'path("finances/", include("apps.finances.api.v1.urls"))' not in source:
        errors.append("Rota canônica /api/v1/finances não está registrada")
    if 'path("financeiro/"' in source or 'include("apps.financeiro' in source:
        errors.append("Rota legada de financeiro voltou ao roteamento global")


def _validate_http_layers(errors: list[str]) -> None:
    for path in (FINANCES / "api" / "v1" / "views").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", source):
            errors.append(f"View v1 acessa ORM diretamente: {_relative(path)}")
        if ".save(" in source or ".delete(" in source or "transaction.atomic" in source:
            errors.append(f"View v1 persiste model diretamente: {_relative(path)}")
    for path in (FINANCES / "api" / "v1" / "serializers").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", source):
            errors.append(f"Serializer v1 acessa ORM diretamente: {_relative(path)}")
        if "transaction.atomic" in source or re.search(r"def\s+(?:create|update)\(", source):
            errors.append(f"Serializer v1 executa caso de uso: {_relative(path)}")


def _validate_exports(errors: list[str]) -> None:
    public_inits = [
        FINANCES / "admin" / "__init__.py",
        FINANCES / "api" / "v1" / "filters" / "__init__.py",
        FINANCES / "api" / "v1" / "permissions" / "__init__.py",
        FINANCES / "api" / "v1" / "serializers" / "__init__.py",
        FINANCES / "api" / "v1" / "views" / "__init__.py",
        FINANCES / "exceptions" / "__init__.py",
        FINANCES / "integrations" / "__init__.py",
        FINANCES / "models" / "__init__.py",
        FINANCES / "selectors" / "__init__.py",
        FINANCES / "services" / "__init__.py",
    ]
    for path in public_inits:
        source = path.read_text(encoding="utf-8")
        if "import *" in source:
            errors.append(f"Export público usa import curinga: {_relative(path)}")
        if "__all__" not in source:
            errors.append(f"Export público sem __all__ explícito: {_relative(path)}")


def validate_finances_architecture(errors: list[str]) -> None:
    _validate_required_paths(errors)
    _validate_app_config(errors)
    _validate_root(errors)
    _validate_removed_legacy(errors)
    _validate_routes(errors)
    _validate_http_layers(errors)
    _validate_exports(errors)
