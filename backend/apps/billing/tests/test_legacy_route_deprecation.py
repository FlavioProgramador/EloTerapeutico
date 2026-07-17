"""Regressões do prefixo legado de Billing durante a janela de transição."""

from __future__ import annotations

import pytest
from django.test import override_settings
from django.urls import reverse

from apps.billing.api.legacy.routes import legacy_billing_route_enabled
from apps.billing.api.legacy.urls import DEFAULT_SUNSET, SUCCESSOR_PATH

pytestmark = pytest.mark.django_db


def test_reverse_uses_canonical_billing_prefix():
    assert reverse("billing-plans") == "/api/v1/billing/plans/"
    assert reverse("legacy-billing-plans") == "/api/billing/plans/"


def test_canonical_route_does_not_emit_deprecation_headers(api_client):
    response = api_client.get(reverse("billing-plans"))

    assert response.status_code == 200
    assert "Deprecation" not in response
    assert "Sunset" not in response
    assert "Warning" not in response


def test_legacy_route_keeps_payload_and_emits_deprecation_headers(api_client):
    canonical = api_client.get(reverse("billing-plans"))
    legacy = api_client.get(reverse("legacy-billing-plans"))

    assert legacy.status_code == canonical.status_code == 200
    assert legacy.data == canonical.data
    assert legacy["Deprecation"] == "true"
    assert legacy["Sunset"] == DEFAULT_SUNSET
    assert legacy["Link"] == f'<{SUCCESSOR_PATH}>; rel="successor-version"'
    assert legacy["Warning"] == '299 - "Deprecated API: use /api/v1/billing/"'


def test_openapi_publishes_only_canonical_billing_prefix(api_client):
    response = api_client.get(reverse("schema"), {"format": "json"})

    assert response.status_code == 200
    paths = response.data["paths"]
    assert "/api/v1/billing/plans/" in paths
    assert "/api/billing/plans/" not in paths


@override_settings(
    BILLING_LEGACY_ROUTE_SUNSET="Mon, 01 Mar 2027 00:00:00 GMT"
)
def test_legacy_route_allows_controlled_sunset_configuration(api_client):
    response = api_client.get(reverse("legacy-billing-plans"))

    assert response["Sunset"] == "Mon, 01 Mar 2027 00:00:00 GMT"


@override_settings(BILLING_LEGACY_ROUTE_ENABLED=False)
def test_django_setting_can_disable_legacy_route():
    assert legacy_billing_route_enabled() is False


@override_settings(BILLING_LEGACY_ROUTE_ENABLED=True)
def test_django_setting_can_keep_legacy_route_during_transition():
    assert legacy_billing_route_enabled() is True


def test_environment_flag_is_parsed_safely(monkeypatch):
    monkeypatch.setenv("BILLING_LEGACY_ROUTE_ENABLED", "false")
    assert legacy_billing_route_enabled() is False

    monkeypatch.setenv("BILLING_LEGACY_ROUTE_ENABLED", "invalid-value")
    assert legacy_billing_route_enabled() is True
