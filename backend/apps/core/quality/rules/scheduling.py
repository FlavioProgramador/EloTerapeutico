"""Regras arquiteturais dedicadas ao domínio de scheduling."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
SCHEDULING = BACKEND / "apps" / "scheduling"
LEGACY_AGENDA = BACKEND / "apps" / "agenda"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _validate_required_paths(errors: list[str]) -> None:
    required = [
        SCHEDULING / "README.md",
        SCHEDULING / "apps.py",
        SCHEDULING / "admin" / "__init__.py",
        SCHEDULING / "admin" / "appointments.py",
        SCHEDULING / "api" / "v1" / "urls.py",
        SCHEDULING / "api" / "legacy" / "urls.py",
        SCHEDULING / "api" / "v1" / "filters" / "__init__.py",
        SCHEDULING / "api" / "v1" / "permissions" / "scheduling.py",
        SCHEDULING / "api" / "v1" / "serializers" / "__init__.py",
        SCHEDULING / "api" / "v1" / "views" / "__init__.py",
        SCHEDULING / "integrations" / "finance.py",
        SCHEDULING / "migrations" / "0001_initial.py",
        SCHEDULING / "models" / "appointments.py",
        SCHEDULING / "selectors" / "conflicts.py",
        SCHEDULING / "selectors" / "resources.py",
        SCHEDULING / "services" / "appointments.py",
        SCHEDULING / "services" / "package_sessions.py",
        SCHEDULING / "services" / "telemedicine.py",
        SCHEDULING / "tests" / "test_scheduling_refactor.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(
                f"Estrutura obrigatória de scheduling ausente: {_relative(path)}"
            )


def _validate_app_config(errors: list[str]) -> None:
    path = SCHEDULING / "apps.py"
    source = path.read_text(encoding="utf-8") if path.exists() else ""
    if 'name = "apps.scheduling"' not in source:
        errors.append("SchedulingConfig não usa o pacote apps.scheduling")
    if 'label = "agenda"' not in source:
        errors.append("SchedulingConfig não preserva o app label agenda")


def _validate_root(errors: list[str]) -> None:
    forbidden = [
        SCHEDULING / "admin.py",
        SCHEDULING / "signals.py",
        SCHEDULING / "models.py",
        SCHEDULING / "services.py",
        SCHEDULING / "selectors.py",
    ]
    for path in forbidden:
        if path.exists():
            errors.append(
                f"Módulo monolítico retornou à raiz de scheduling: {_relative(path)}"
            )


def _validate_legacy_package(errors: list[str]) -> None:
    if (LEGACY_AGENDA / "migrations").exists():
        errors.append("apps.agenda não pode manter migrations após a renomeação")
    if (LEGACY_AGENDA / "signals.py").exists():
        errors.append("Placeholder apps.agenda.signals.py não deve existir")

    facade_roots = [
        LEGACY_AGENDA / "admin.py",
        LEGACY_AGENDA / "apps.py",
        LEGACY_AGENDA / "urls.py",
        LEGACY_AGENDA / "models",
        LEGACY_AGENDA / "services",
        LEGACY_AGENDA / "selectors",
        LEGACY_AGENDA / "exceptions",
        LEGACY_AGENDA / "api",
    ]
    for root in facade_roots:
        paths = [root] if root.is_file() else list(root.rglob("*.py")) if root.exists() else []
        for path in paths:
            line_count = len(path.read_text(encoding="utf-8").splitlines())
            if line_count > 80:
                errors.append(
                    "Fachada de compatibilidade de agenda contém implementação "
                    f"excessiva: {_relative(path)} ({line_count} linhas)"
                )


def _validate_routes(errors: list[str]) -> None:
    path = BACKEND / "config" / "urls.py"
    source = path.read_text(encoding="utf-8") if path.exists() else ""
    if 'path("scheduling/", include("apps.scheduling.api.v1.urls"))' not in source:
        errors.append("Rota canônica /api/v1/scheduling não está registrada")
    if 'path("agenda/", include("apps.scheduling.api.legacy.urls"))' not in source:
        errors.append("Alias legado /api/v1/agenda não está registrado")
    if 'include("apps.agenda.urls")' in source:
        errors.append("Roteamento global ainda depende de apps.agenda.urls")


def _validate_v1_views(errors: list[str]) -> None:
    root = SCHEDULING / "api" / "v1" / "views"
    if not root.exists():
        return
    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", source):
            errors.append(f"View v1 acessa ORM diretamente: {_relative(path)}")
        if ".save(" in source or ".delete(" in source:
            errors.append(f"View v1 altera model diretamente: {_relative(path)}")
        if "apps.financeiro" in source or "apps.communications" in source:
            errors.append(
                f"View v1 importa integração externa diretamente: {_relative(path)}"
            )


def _validate_exports(errors: list[str]) -> None:
    public_inits = [
        SCHEDULING / "admin" / "__init__.py",
        SCHEDULING / "api" / "v1" / "filters" / "__init__.py",
        SCHEDULING / "api" / "v1" / "permissions" / "__init__.py",
        SCHEDULING / "api" / "v1" / "serializers" / "__init__.py",
        SCHEDULING / "api" / "v1" / "views" / "__init__.py",
        SCHEDULING / "models" / "__init__.py",
        SCHEDULING / "selectors" / "__init__.py",
        SCHEDULING / "services" / "__init__.py",
    ]
    for path in public_inits:
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        if "import *" in source:
            errors.append(f"Export público usa import curinga: {_relative(path)}")
        if "__all__" not in source:
            errors.append(f"Export público sem __all__ explícito: {_relative(path)}")


def validate_scheduling_architecture(errors: list[str]) -> None:
    """Acrescenta violações arquiteturais específicas de scheduling."""

    _validate_required_paths(errors)
    _validate_app_config(errors)
    _validate_root(errors)
    _validate_legacy_package(errors)
    _validate_routes(errors)
    _validate_v1_views(errors)
    _validate_exports(errors)
