"""Regra arquitetural dedicada ao app core."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
CORE = BACKEND / "apps" / "core"

DOMAIN_APPS = (
    "agenda",
    "billing",
    "communications",
    "documents",
    "financeiro",
    "forms",
    "patients",
    "records",
    "reports",
)
DOMAIN_IMPORT_PATTERN = re.compile(
    rf"(?m)^\s*(?:from|import)\s+apps\.({'|'.join(DOMAIN_APPS)})(?:\.|\s|$)"
)


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _validate_required_paths(errors: list[str]) -> None:
    required_paths = [
        CORE / "admin" / "__init__.py",
        CORE / "admin" / "dashboard.py",
        CORE / "admin" / "sql.py",
        CORE / "admin" / "unfold.py",
        CORE / "api" / "exceptions.py",
        CORE / "api" / "urls.py",
        CORE / "api" / "views" / "__init__.py",
        CORE / "api" / "views" / "health.py",
        CORE / "exceptions" / "__init__.py",
        CORE / "fields" / "__init__.py",
        CORE / "fields" / "encrypted.py",
        CORE / "health" / "__init__.py",
        CORE / "health" / "checks.py",
        CORE / "health" / "services.py",
        CORE / "validators" / "__init__.py",
        CORE / "validators" / "identifiers.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(f"Estrutura obrigatória do core ausente: {_relative(path)}")


def _validate_removed_monoliths(errors: list[str]) -> None:
    forbidden_paths = [
        CORE / "admin_unfold.py",
        CORE / "exceptions.py",
        CORE / "fields.py",
        CORE / "health.py",
        CORE / "health_urls.py",
        CORE / "validators.py",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"Módulo monolítico retornou à raiz do core: {_relative(path)}")


def _validate_compatibility_facades(errors: list[str]) -> None:
    facades = [
        CORE / "admin_dashboard.py",
        CORE / "admin_sql.py",
    ]
    for path in facades:
        if not path.exists():
            errors.append(f"Fachada de compatibilidade do core ausente: {_relative(path)}")
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 80:
            errors.append(
                "Fachada de compatibilidade do core contém implementação excessiva: "
                f"{_relative(path)} ({line_count} linhas)"
            )


def _validate_core_dependency_direction(errors: list[str]) -> None:
    ignored_roots = {"admin", "quality", "tests"}
    for path in CORE.rglob("*.py"):
        relative_parts = path.relative_to(CORE).parts
        if relative_parts and relative_parts[0] in ignored_roots:
            continue
        source = path.read_text(encoding="utf-8")
        if DOMAIN_IMPORT_PATTERN.search(source):
            errors.append(
                "Core importa app de domínio diretamente fora da camada administrativa: "
                f"{_relative(path)}"
            )


def _validate_core_views(errors: list[str]) -> None:
    views_root = CORE / "api" / "views"
    if not views_root.exists():
        return
    for path in views_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", source):
            errors.append(f"View do core acessa ORM diretamente: {_relative(path)}")
        if re.search(r"(?m)^\s*(?:from|import)\s+.*infrastructure", source):
            errors.append(f"View do core importa infraestrutura diretamente: {_relative(path)}")


def _validate_core_routes(errors: list[str]) -> None:
    urls = BACKEND / "config" / "urls.py"
    if not urls.exists():
        errors.append(f"Arquivo de URLs global ausente: {_relative(urls)}")
        return
    source = urls.read_text(encoding="utf-8")
    if 'include("apps.core.api.urls")' not in source:
        errors.append("Health checks globais não usam o roteamento canônico apps.core.api.urls")
    if "apps.core.health_urls" in source:
        errors.append("Roteamento global ainda referencia apps.core.health_urls")


def validate_core_architecture(errors: list[str]) -> None:
    """Acrescenta ao relatório as violações arquiteturais específicas do core."""

    _validate_required_paths(errors)
    _validate_removed_monoliths(errors)
    _validate_compatibility_facades(errors)
    _validate_core_dependency_direction(errors)
    _validate_core_views(errors)
    _validate_core_routes(errors)
