"""Testes de fumaça e limites arquiteturais do backend."""

from importlib import import_module
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize(
    "module_name",
    [
        "apps.core.fields",
        "apps.core.api.pagination",
        "apps.core.validators",
        "apps.communications.infrastructure.messaging.email",
        "apps.communications.api.v1.urls",
        "apps.communications.api.v1.serializers",
        "apps.communications.api.v1.permissions",
        "apps.communications.api.public.urls",
        "apps.communications.integrations.providers",
        "apps.communications.selectors",
        "apps.communications.signals",
        "apps.communications.tasks",
        "apps.communications.validators",
        "apps.communications.admin",
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
        "apps.patients.models",
        "apps.patients.services.imports",
        "apps.records.api.evolution_serializers",
        "apps.records.api.evolution_views",
        "apps.records.models",
        "apps.records.selectors.evolutions",
        "apps.records.services.evolutions",
        "apps.agenda.api.urls",
        "apps.agenda.models",
        "apps.agenda.selectors.appointments",
        "apps.agenda.selectors.availability",
        "apps.agenda.services.appointments",
        "apps.agenda.services.packages",
        "apps.agenda.services.recurrences",
        "apps.documents.models",
        "apps.documents.selectors.document_templates",
        "apps.documents.services.generated_documents",
        "apps.documents.serializers",
        "apps.documents.views",
        "apps.forms.models",
        "apps.forms.selectors.therapeutic_forms",
        "apps.forms.services.therapeutic_forms",
        "apps.forms.services.submissions",
        "apps.forms.serializers",
        "apps.forms.views",
        "apps.financeiro.api.transaction_viewset",
        "apps.financeiro.api.urls",
        "apps.financeiro.models",
        "apps.financeiro.selectors.transactions",
        "apps.financeiro.services.exports",
        "apps.financeiro.services.payments",
        "apps.reports.selectors.appointments",
        "apps.reports.selectors.financial_transactions",
        "apps.reports.services.appointment_reports",
        "apps.reports.services.financial_reports",
        "apps.reports.views",
    ],
)
def test_backend_modules_import_without_cycles(module_name):
    assert import_module(module_name) is not None


@pytest.mark.parametrize(
    "public_module",
    [
        "apps.users.urls",
        "apps.patients.urls",
        "apps.records.urls",
        "apps.agenda.urls",
        "apps.documents.urls",
        "apps.forms.urls",
        "apps.financeiro.urls",
        "apps.reports.urls",
        "apps.communications.urls",
        "apps.communications.urls_public",
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
        "apps/communications/api/v1/serializers/__init__.py",
        "apps/communications/api/v1/permissions/__init__.py",
        "apps/communications/integrations/providers/__init__.py",
        "apps/communications/selectors/__init__.py",
        "apps/communications/tasks/__init__.py",
        "apps/communications/signals/__init__.py",
        "apps/communications/validators/__init__.py",
        "apps/communications/admin/__init__.py",
        "apps/documents/models/__init__.py",
        "apps/documents/selectors/__init__.py",
        "apps/documents/services/__init__.py",
        "apps/documents/serializers/__init__.py",
        "apps/documents/views/__init__.py",
        "apps/forms/models/__init__.py",
        "apps/forms/selectors/__init__.py",
        "apps/forms/services/__init__.py",
        "apps/forms/serializers/__init__.py",
        "apps/forms/views/__init__.py",
        "apps/reports/selectors/__init__.py",
        "apps/reports/services/__init__.py",
        "apps/reports/views/__init__.py",
        "apps/users/api/serializers.py",
        "apps/users/api/views.py",
    ],
)
def test_public_exports_are_explicit(relative_path):
    source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
    assert "import *" not in source


@pytest.mark.parametrize(
    "relative_path",
    [
        "apps/agenda/models.py",
        "apps/agenda/model_parts",
        "apps/agenda/services/core_services.py",
        "apps/communications/admin.py",
        "apps/communications/selectors.py",
        "apps/communications/signals.py",
        "apps/communications/tasks.py",
        "apps/communications/validators.py",
        "apps/documents/models.py",
        "apps/documents/model_parts",
        "apps/documents/services/core_services.py",
        "apps/forms/models.py",
        "apps/forms/model_parts",
        "apps/forms/api/serializers/forms_serializers.py",
        "apps/forms/api/views/forms_views.py",
        "apps/financeiro/models.py",
        "apps/financeiro/model_parts",
        "apps/patients/models.py",
        "apps/patients/model_parts",
        "apps/reports/services/core_services.py",
        "apps/users/views.py",
        "apps/users/serializers.py",
        "apps/patients/dashboard_actions.py",
        "apps/patients/export_actions.py",
        "apps/patients/form_actions.py",
        "apps/patients/invite_actions.py",
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


def test_communications_compatibility_facades_remain_thin():
    facade_paths = [
        "apps/communications/channel_serializers.py",
        "apps/communications/permissions.py",
        "apps/communications/providers.py",
        "apps/communications/serializers.py",
        "apps/communications/urls.py",
        "apps/communications/urls_public.py",
    ]
    for relative_path in facade_paths:
        source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 80, relative_path


def test_communications_migration_operations_path_is_preserved():
    path = BACKEND_ROOT / "apps/communications/migration_operations.py"
    assert path.exists()
    module = import_module("apps.communications.migration_operations")
    assert hasattr(module, "CreateModelIfNotExists")
