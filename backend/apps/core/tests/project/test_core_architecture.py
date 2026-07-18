"""Testes das fronteiras arquiteturais específicas do app core."""

from importlib import import_module
from pathlib import Path

import pytest

from apps.core.quality.rules.core import validate_core_architecture

BACKEND_ROOT = Path(__file__).resolve().parents[4]
CORE_ROOT = BACKEND_ROOT / "apps" / "core"


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.core.admin",
        "apps.core.admin.dashboard",
        "apps.core.admin.sql",
        "apps.core.admin.unfold",
        "apps.core.api.exceptions",
        "apps.core.api.urls",
        "apps.core.api.views.health",
        "apps.core.exceptions",
        "apps.core.fields",
        "apps.core.fields.encrypted",
        "apps.core.health",
        "apps.core.health.checks",
        "apps.core.health.services",
        "apps.core.validators",
        "apps.core.validators.identifiers",
    ],
)
def test_core_modules_import_without_cycles(module_name: str):
    assert import_module(module_name) is not None


def test_core_architecture_rule_accepts_current_tree():
    errors: list[str] = []
    validate_core_architecture(errors)
    assert errors == []


@pytest.mark.parametrize(
    "relative_path",
    [
        "admin_unfold.py",
        "exceptions.py",
        "fields.py",
        "health_urls.py",
        "validators.py",
    ],
)
def test_core_monoliths_do_not_return_to_root(relative_path: str):
    assert not (CORE_ROOT / relative_path).exists()


@pytest.mark.parametrize(
    "relative_path",
    [
        "admin_dashboard.py",
        "admin_sql.py",
        "health.py",
    ],
)
def test_core_compatibility_facades_remain_thin(relative_path: str):
    source = (CORE_ROOT / relative_path).read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 80


def test_health_routes_keep_public_contract():
    module = import_module("apps.core.api.urls")
    assert [pattern.name for pattern in module.urlpatterns] == [
        "health-live",
        "health-ready",
    ]
