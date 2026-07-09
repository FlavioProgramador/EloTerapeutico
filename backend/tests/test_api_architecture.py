"""Testes de fumaça e limites arquiteturais do backend."""

from importlib import import_module
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    [
        "core.fields",
        "core.pagination",
        "core.validators",
        "infrastructure.notifications",
        "apps.users.api.serializers",
        "apps.users.api.views",
        "apps.users.services.password_reset",
        "apps.patients.actions.dashboard",
        "apps.patients.actions.exports",
        "apps.patients.actions.forms",
        "apps.patients.actions.imports",
        "apps.patients.actions.invites",
        "apps.patients.actions.metrics",
        "apps.patients.api.urls",
        "apps.patients.services.imports",
        "apps.records.api.evolution_serializers",
        "apps.records.api.evolution_views",
        "apps.records.models",
        "apps.records.selectors.evolutions",
        "apps.records.services.evolutions",
        "apps.agenda.api.urls",
        "apps.financeiro.api.transaction_viewset",
        "apps.financeiro.api.urls",
        "apps.financeiro.selectors.transactions",
        "apps.financeiro.services.exports",
        "apps.financeiro.services.payments",
    ],
)
def test_backend_modules_import_without_cycles(module_name):
    assert import_module(module_name) is not None


@pytest.mark.parametrize(
    "public_module",
    [
        "apps.users.urls",
        "apps.users.health_urls",
        "apps.patients.urls",
        "apps.records.urls",
        "apps.agenda.urls",
        "apps.financeiro.urls",
    ],
)
def test_public_url_modules_keep_their_contract(public_module):
    assert import_module(public_module).urlpatterns


@pytest.mark.parametrize(
    "relative_path",
    [
        "apps/agenda/api/models.py",
        "apps/agenda/api/serializers/__init__.py",
        "apps/agenda/api/views/__init__.py",
        "apps/users/api/serializers.py",
        "apps/users/api/views.py",
    ],
)
def test_api_exports_are_explicit(relative_path):
    source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
    assert "import *" not in source


@pytest.mark.parametrize(
    "relative_path",
    [
        "apps/users/views.py",
        "apps/users/serializers.py",
        "apps/patients/dashboard_actions.py",
        "apps/patients/export_actions.py",
        "apps/patients/form_actions.py",
        "apps/patients/invite_actions.py",
        "apps/records/models.py",
        "apps/financeiro/views.py",
        "apps/financeiro/serializers.py",
        "apps/financeiro/filters.py",
        "apps/records/evolution_flow_views.py",
        "apps/records/evolution_flow_views_v2.py",
        "apps/records/evolution_flow_serializers_v2.py",
    ],
)
def test_moved_modules_do_not_return_to_app_root(relative_path):
    assert not (BACKEND_ROOT / relative_path).exists()
