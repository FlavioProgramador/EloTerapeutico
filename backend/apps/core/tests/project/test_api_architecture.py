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
        "apps.billing.models",
        "apps.billing.api.v1.urls",
        "apps.billing.api.v1.serializers",
        "apps.billing.api.v1.views",
        "apps.billing.api.v1.permissions",
        "apps.billing.api.public.registration",
        "apps.billing.api.public.webhooks",
        "apps.billing.api.legacy.routes",
        "apps.billing.api.legacy.urls",
        "apps.billing.authentication",
        "apps.billing.checks",
        "apps.billing.security",
        "apps.billing.views",
        "apps.billing.integrations.webhooks.asaas",
        "apps.billing.tasks",
        "apps.billing.admin",
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
        "apps.scheduling.api.urls",
        "apps.scheduling.models",
        "apps.scheduling.selectors.appointments",
        "apps.scheduling.selectors.availability",
        "apps.scheduling.services.appointments",
        "apps.scheduling.services.packages",
        "apps.scheduling.services.recurrences",
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
        "apps.finances.api.v1.views",
        "apps.finances.api.v1.urls",
        "apps.finances.models",
        "apps.finances.selectors",
        "apps.finances.services.exports",
        "apps.finances.services.payments",
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
        "apps.scheduling.urls",
        "apps.documents.urls",
        "apps.forms.urls",
        "apps.finances.api.v1.urls",
        "apps.reports.urls",
        "apps.billing.api.v1.urls",
        "apps.billing.api.legacy.urls",
        "apps.communications.urls",
        "apps.communications.urls_public",
    ],
)
def test_public_url_modules_keep_their_contract(public_module):
    assert import_module(public_module).urlpatterns


@pytest.mark.parametrize(
    "relative_path",
    [
        "apps/billing/models/__init__.py",
        "apps/billing/api/v1/serializers/__init__.py",
        "apps/billing/api/v1/views/__init__.py",
        "apps/billing/api/v1/permissions/__init__.py",
        "apps/billing/api/legacy/__init__.py",
        "apps/billing/authentication/__init__.py",
        "apps/billing/checks/__init__.py",
        "apps/billing/security/__init__.py",
        "apps/billing/tasks/__init__.py",
        "apps/billing/admin/__init__.py",
        "apps/billing/views/__init__.py",
        "apps/billing/integrations/webhooks/asaas/__init__.py",
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
        "apps/finances/models/__init__.py",
        "apps/finances/selectors/__init__.py",
        "apps/finances/services/__init__.py",
        "apps/finances/admin/__init__.py",
        "apps/finances/api/v1/serializers/__init__.py",
        "apps/finances/api/v1/views/__init__.py",
        "apps/finances/api/v1/permissions/__init__.py",
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
        "apps/billing/access_views.py",
        "apps/billing/admin.py",
        "apps/billing/authentication.py",
        "apps/billing/checkout_views.py",
        "apps/billing/checks.py",
        "apps/billing/decorators.py",
        "apps/billing/legacy_route.py",
        "apps/billing/legacy_urls.py",
        "apps/billing/models.py",
        "apps/billing/permissions.py",
        "apps/billing/registration.py",
        "apps/billing/security.py",
        "apps/billing/serializers.py",
        "apps/billing/tasks.py",
        "apps/billing/urls.py",
        "apps/billing/views.py",
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
        "apps/finances/models.py",
        "apps/finances/model_parts",
        "apps/patients/models.py",
        "apps/patients/model_parts",
        "apps/reports/services/core_services.py",
        "apps/users/views.py",
        "apps/users/serializers.py",
        "apps/patients/dashboard_actions.py",
        "apps/patients/export_actions.py",
        "apps/patients/form_actions.py",
        "apps/patients/invite_actions.py",
        "apps/finances/views.py",
        "apps/finances/serializers.py",
        "apps/finances/filters.py",
        "apps/records/evolution_flow_views.py",
        "apps/records/evolution_flow_views_v2.py",
        "apps/records/evolution_flow_serializers_v2.py",
    ],
)
def test_moved_modules_do_not_return_to_app_root(relative_path):
    assert not (BACKEND_ROOT / relative_path).exists()


def test_legacy_agenda_package_is_removed():
    assert not (BACKEND_ROOT / "apps/agenda").exists()
    with pytest.raises(ModuleNotFoundError):
        import_module("apps.agenda")


def _assert_facades_are_thin(paths: list[str]) -> None:
    for relative_path in paths:
        source = (BACKEND_ROOT / relative_path).read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 80, relative_path


def test_billing_root_contains_only_entrypoint_files():
    app_root = BACKEND_ROOT / "apps/billing"
    root_files = {path.name for path in app_root.iterdir() if path.is_file()}
    assert root_files == {"README.md", "__init__.py", "apps.py"}


def test_billing_compatibility_packages_remain_thin():
    _assert_facades_are_thin(
        [
            "apps/billing/authentication/__init__.py",
            "apps/billing/views/__init__.py",
            "apps/billing/webhooks/asaas.py",
        ]
    )


def test_billing_task_names_remain_public():
    tasks = import_module("apps.billing.tasks")
    assert tasks.process_webhook_event_task.name == (
        "apps.billing.tasks.process_webhook_event"
    )
    assert tasks.dispatch_pending_webhook_events.name == (
        "apps.billing.tasks.dispatch_pending_webhook_events"
    )
    assert tasks.reconcile_asaas_payments.name == (
        "apps.billing.tasks.reconcile_asaas_payments"
    )


def test_billing_webhook_facade_preserves_patch_points():
    module = import_module("apps.billing.webhooks.asaas")
    assert callable(module.activate_subscription_from_payment)
    assert callable(module.mark_subscription_past_due)


def test_legacy_financeiro_package_is_removed():
    assert not (BACKEND_ROOT / "apps/financeiro").exists()
    with pytest.raises(ModuleNotFoundError):
        import_module("apps.financeiro")


def test_finances_root_contains_only_entrypoint_files():
    app_root = BACKEND_ROOT / "apps/finances"
    root_files = {path.name for path in app_root.iterdir() if path.is_file()}
    assert root_files == {"README.md", "__init__.py", "apps.py"}
