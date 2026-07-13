from __future__ import annotations

import pytest
from django.db import OperationalError
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_database_not_ready_returns_service_unavailable(monkeypatch):
    user = User.objects.create_user(
        email="communications.readiness@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Readiness",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    client = APIClient()
    client.force_authenticate(user)

    def raise_database_error(_owner):
        raise OperationalError("communications table unavailable")

    monkeypatch.setattr(
        "apps.communications.permissions.enforce_communication_access",
        raise_database_error,
    )

    response = client.get("/api/v1/communications/")

    assert response.status_code == 503
    assert response.data == {
        "error": {
            "code": "COMMUNICATIONS_DATABASE_NOT_READY",
            "message": (
                "O banco do módulo de Comunicações ainda não está disponível. "
                "Aplique as migrations do backend e reinicie os serviços."
            ),
            "details": None,
        }
    }
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert response["X-Request-ID"]
