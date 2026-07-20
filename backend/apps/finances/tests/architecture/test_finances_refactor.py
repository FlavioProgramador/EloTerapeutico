"""Contratos de renomeação segura e arquitetura de finances."""

from importlib import import_module
from pathlib import Path

import pytest
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from apps.finances.models import FinancialTransaction, MonthlySubscription

BACKEND = Path(__file__).resolve().parents[4]


@pytest.mark.django_db
def test_package_name_preserves_historical_django_identity():
    config = apps.get_app_config("financeiro")
    assert config.name == "apps.finances"
    assert config.label == "financeiro"
    assert FinancialTransaction._meta.app_label == "financeiro"
    assert MonthlySubscription._meta.app_label == "financeiro"
    assert FinancialTransaction._meta.db_table.startswith("financeiro_")
    assert MonthlySubscription._meta.db_table.startswith("financeiro_")
    assert not FinancialTransaction._meta.db_table.startswith("finances_")
    assert ContentType.objects.get_for_model(FinancialTransaction).app_label == "financeiro"


def test_legacy_python_package_is_removed():
    assert not (BACKEND / "apps/financeiro").exists()
    with pytest.raises(ModuleNotFoundError):
        import_module("apps.financeiro")


def test_canonical_routes_keep_router_names():
    assert reverse("transaction-list") == "/api/v1/finances/"
    assert reverse("transaction-summary") == "/api/v1/finances/summary/"


def test_admin_url_keeps_historical_label():
    assert reverse("admin:financeiro_financialtransaction_changelist").startswith("/admin/financeiro/")
