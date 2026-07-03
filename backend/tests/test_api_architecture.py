"""Testes de fumaça e limites arquiteturais da API."""

from importlib import import_module
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.patients.api.filters",
        "apps.patients.api.serializers",
        "apps.patients.api.views",
        "apps.patients.api.urls",
        "apps.agenda.api.filters",
        "apps.agenda.api.serializers",
        "apps.agenda.api.views",
        "apps.agenda.api.urls",
        "apps.financeiro.api.filters",
        "apps.financeiro.api.serializers",
        "apps.financeiro.api.views",
        "apps.financeiro.api.urls",
    ],
)
def test_api_modules_import_without_cycles(module_name):
    assert import_module(module_name) is not None


@pytest.mark.parametrize(
    "legacy_module",
    [
        "apps.patients.urls",
        "apps.agenda.urls",
        "apps.financeiro.urls",
    ],
)
def test_public_url_modules_keep_their_contract(legacy_module):
    module = import_module(legacy_module)
    assert module.urlpatterns


@pytest.mark.parametrize(
    "relative_path",
    [
        "apps/patients/api/models.py",
        "apps/agenda/api/models.py",
        "apps/financeiro/api/models.py",
    ],
)
def test_api_layer_does_not_shadow_domain_models(relative_path):
    assert not (BACKEND_ROOT / relative_path).exists()


def test_records_does_not_keep_evolution_view_wrapper():
    wrapper = BACKEND_ROOT / "apps/records/evolution_flow_views.py"
    assert not wrapper.exists()
