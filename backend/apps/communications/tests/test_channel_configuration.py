from __future__ import annotations

import pytest
from django.core import mail
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.users.models import User

from ..models import CommunicationChannelConfig
from ..services import ensure_default_channels


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="channel.config@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Canais",
        role=User.Role.THERAPIST,
        phone="+5521999998888",
        onboarding_completed_at=timezone.now(),
    )


@pytest.fixture
def authenticated_client(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    return client


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_channel_catalog_does_not_expose_internal_requirements(
    authenticated_client,
    therapist,
):
    ensure_default_channels(therapist)
    response = authenticated_client.get("/api/v1/communications/channels/")

    assert response.status_code == 200
    serialized = str(response.data)
    assert "internal_requirements" not in serialized
    assert "admin_instructions" not in serialized
    assert "deployment_notes" not in serialized
    assert "EMAIL_BACKEND" not in serialized
    assert "DEFAULT_FROM_EMAIL" not in serialized
    assert "variáveis de ambiente" not in serialized


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_smtp_secret_is_encrypted_masked_and_preserved(authenticated_client, therapist):
    ensure_default_channels(therapist)
    response = authenticated_client.patch(
        "/api/v1/communications/channels/email/",
        {
            "provider": "smtp",
            "metadata": {
                "host": "smtp.example.test",
                "port": 587,
                "use_tls": True,
                "use_ssl": False,
                "sender_name": "Clínica Teste",
                "sender_email": "noreply@example.test",
            },
            "secrets": {"username": "smtp-user", "password": "smtp-password"},
            "save_as_draft": True,
            "confirm_provider_change": True,
        },
        format="json",
    )
    assert response.status_code == 200
    assert "secrets" not in response.data
    assert response.data["credential_state"] == {"username": True, "password": True}
    assert response.data["connection_status"] == CommunicationChannelConfig.ConnectionStatus.INCOMPLETE

    config = CommunicationChannelConfig.objects.get(owner=therapist, channel="email")
    assert config.get_credentials()["password"] == "smtp-password"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT credentials FROM communications_communicationchannelconfig WHERE id = %s",
            [config.pk],
        )
        raw_value = cursor.fetchone()[0]
    assert "smtp-password" not in raw_value

    second_response = authenticated_client.patch(
        "/api/v1/communications/channels/email/",
        {
            "provider": "smtp",
            "metadata": {
                **config.metadata,
                "timeout": 20,
            },
            "secrets": {},
            "save_as_draft": True,
        },
        format="json",
    )
    assert second_response.status_code == 200
    config.refresh_from_db()
    assert config.get_credentials()["password"] == "smtp-password"


@pytest.mark.django_db
@override_settings(
    BILLING_REQUIRE_SUBSCRIPTION=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@example.test",
)
def test_default_email_can_be_validated_and_tested(authenticated_client, therapist):
    ensure_default_channels(therapist)
    validation = authenticated_client.post(
        "/api/v1/communications/channels/email/test-connection/",
        {},
        format="json",
    )
    assert validation.status_code == 200
    assert validation.data["connection_status"] == CommunicationChannelConfig.ConnectionStatus.CONFIGURED

    test_message = authenticated_client.post(
        "/api/v1/communications/channels/email/test/",
        {"destination": "delivery@example.test"},
        format="json",
    )
    assert test_message.status_code == 202
    assert test_message.data["test"]["success"] is True
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["delivery@example.test"]


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_incomplete_external_channel_cannot_be_activated(authenticated_client, therapist):
    ensure_default_channels(therapist)
    response = authenticated_client.patch(
        "/api/v1/communications/channels/sms/",
        {
            "provider": "twilio",
            "metadata": {"account_sid": "AC123", "sender": "+15550001111"},
            "save_as_draft": True,
        },
        format="json",
    )
    assert response.status_code == 200
    activation = authenticated_client.post(
        "/api/v1/communications/channels/sms/activate/",
        {},
        format="json",
    )
    assert activation.status_code == 400


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_active_provider_change_requires_explicit_confirmation(authenticated_client, therapist):
    ensure_default_channels(therapist)
    config = CommunicationChannelConfig.objects.get(owner=therapist, channel="email")
    config.is_active = True
    config.save(update_fields=["is_active", "updated_at"])

    payload = {
        "provider": "smtp",
        "metadata": {
            "host": "smtp.example.test",
            "port": 587,
            "use_tls": True,
            "use_ssl": False,
            "sender_name": "Clínica Teste",
            "sender_email": "noreply@example.test",
        },
        "secrets": {"username": "user", "password": "password"},
        "save_as_draft": True,
    }
    rejected = authenticated_client.patch(
        "/api/v1/communications/channels/email/",
        payload,
        format="json",
    )
    assert rejected.status_code == 400

    accepted = authenticated_client.patch(
        "/api/v1/communications/channels/email/",
        {**payload, "confirm_provider_change": True},
        format="json",
    )
    assert accepted.status_code == 200
    assert accepted.data["provider"] == "smtp"
    assert accepted.data["is_active"] is False
