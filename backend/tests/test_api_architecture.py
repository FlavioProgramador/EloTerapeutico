"""Testes de fumaça para a organização modular da API."""

from importlib import import_module

import pytest


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
def test_legacy_url_modules_keep_compatibility(legacy_module):
    module = import_module(legacy_module)
    assert module.urlpatterns
