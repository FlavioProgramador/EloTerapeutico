from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.billing.models import Plan, Subscription
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
)
from apps.patients.models import Patient
from apps.scheduling.exceptions import (
    TelemedicineAccessDeniedError,
    TelemedicineConsentRequiredError,
    TelemedicineInvitationExpiredError,
)
from apps.scheduling.models import (
    Appointment,
    TelemedicineConsent,
    TelemedicineInvitation,
    TelemedicineParticipantSession,
    TelemedicineRoom,
    TelemedicineWebhookEvent,
)
from apps.scheduling.selectors.telemedicine import invitation_token_hash
from apps.scheduling.services.telemedicine import (
    create_patient_invitation,
    exchange_patient_invitation,
    issue_patient_join_credentials,
    process_telemedicine_webhook,
    record_telemedicine_consent,
)
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def telemedicine_environment(monkeypatch, settings):
    settings.DEBUG = True
    monkeypatch.setenv("TELEMEDICINE_ENABLED", "True")
    monkeypatch.setenv("TELEMEDICINE_PROVIDER", "fake")
    monkeypatch.setenv("TELEMEDICINE_REQUIRE_E2EE", "True")
    monkeypatch.setenv("TELEMEDICINE_JOIN_BEFORE_MINUTES", "15")
    monkeypatch.setenv("TELEMEDICINE_JOIN_AFTER_MINUTES", "30")
    monkeypatch.setenv("TELEMEDICINE_PROVIDER_TOKEN_TTL_SECONDS", "300")
    monkeypatch.setenv("TELEMEDICINE_MAX_PARTICIPANTS", "2")


def create_context(*, suffix: str = "principal", telemedicine_plan: bool = True):
    therapist = User.objects.create_user(
        email=f"terapeuta-{suffix}@example.test",
        full_name=f"Terapeuta {suffix.title()}",
        password="TestPass2026!",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name=f"Clínica {suffix.title()}",
        slug=f"clinica-{suffix}",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=therapist,
    )
    OrganizationSettings.objects.create(
        organization=organization,
        allow_telemedicine=True,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=therapist,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=False,
    )
    plan = Plan.objects.create(
        name=f"Plano {suffix.title()}",
        slug=f"plano-{suffix}",
        price=Decimal("99.00"),
        has_telemedicine=telemedicine_plan,
    )
    now = timezone.now()
    Subscription.objects.create(
        user=therapist,
        plan=plan,
        status=Subscription.Status.ACTIVE,
        started_at=now - timedelta(days=1),
        access_starts_at=now - timedelta(days=1),
        access_ends_at=now + timedelta(days=30),
    )
    patient = Patient.objects.create(
        organization=organization,
        therapist=therapist,
        full_name=f"Paciente {suffix.title()}",
    )
    start = now + timedelta(minutes=5)
    appointment = Appointment.objects.create(
        organization=organization,
        patient=patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        status=Appointment.Status.CONFIRMED,
        modality=Appointment.Modality.ONLINE,
        session_value=Decimal("150.00"),
        created_by=therapist,
        updated_by=therapist,
    )
    room = TelemedicineRoom.objects.get(appointment=appointment)
    return therapist, organization, patient, appointment, room


def authenticated_client(*, therapist, organization):
    client = APIClient()
    client.force_authenticate(therapist)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))
    return client


def test_online_appointment_creates_exactly_one_tenant_room():
    _, organization, _, appointment, room = create_context()

    assert room.organization == organization
    assert room.appointment == appointment
    assert TelemedicineRoom.objects.filter(appointment=appointment).count() == 1
    assert room.provider_room_name.startswith("tm_")
    assert str(appointment.pk) not in room.provider_room_name


def test_invitation_persists_only_hash_and_regeneration_revokes_previous():
    therapist, _, _, _, room = create_context()

    first, first_token, first_url = create_patient_invitation(
        actor=therapist,
        room=room,
    )
    second, second_token, second_url = create_patient_invitation(
        actor=therapist,
        room=room,
    )
    first.refresh_from_db()

    assert first.revoked_at is not None
    assert second.revoked_at is None
    assert first.token_hash == invitation_token_hash(first_token)
    assert second.token_hash == invitation_token_hash(second_token)
    assert first_token not in first.token_hash
    assert second_token not in second.token_hash
    assert "#token=" in first_url
    assert "#token=" in second_url
    assert TelemedicineInvitation.objects.filter(
        room=room,
        revoked_at__isnull=True,
    ).count() == 1


def test_patient_requires_versioned_consent_before_ephemeral_credentials():
    therapist, _, _, _, room = create_context()
    _, raw_token, _ = create_patient_invitation(actor=therapist, room=room)

    public_context = exchange_patient_invitation(raw_token=raw_token)
    assert public_context["consent_accepted"] is False
    assert public_context["recording_enabled"] is False
    assert "patient_name" not in public_context
    assert "notes" not in public_context

    with pytest.raises(TelemedicineConsentRequiredError):
        issue_patient_join_credentials(raw_token=raw_token)

    consent = record_telemedicine_consent(
        raw_token=raw_token,
        accepted=True,
    )
    credentials = issue_patient_join_credentials(raw_token=raw_token)

    assert consent.document_version
    assert len(consent.document_hash) == 64
    assert credentials["token"].startswith("fake.")
    assert credentials["role"] == "patient"
    assert credentials["recording_enabled"] is False
    assert credentials["e2ee_enabled"] is True
    assert credentials["e2ee_key"]
    assert not TelemedicineInvitation.objects.filter(
        token_hash=credentials["token"]
    ).exists()


def test_e2ee_key_is_encrypted_at_rest():
    therapist, _, _, _, room = create_context()
    _, raw_token, _ = create_patient_invitation(actor=therapist, room=room)
    record_telemedicine_consent(raw_token=raw_token, accepted=True)
    credentials = issue_patient_join_credentials(raw_token=raw_token)
    room.refresh_from_db()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT e2ee_key FROM agenda_telemedicineroom WHERE id = %s",
            [room.pk],
        )
        stored_value = cursor.fetchone()[0]

    assert room.e2ee_key == credentials["e2ee_key"]
    assert stored_value != credentials["e2ee_key"]
    assert str(stored_value).startswith("gAAAA")


def test_revoked_invitation_cannot_be_exchanged():
    therapist, _, _, _, room = create_context()
    invitation, raw_token, _ = create_patient_invitation(actor=therapist, room=room)
    invitation.revoked_at = timezone.now()
    invitation.save(update_fields=["revoked_at", "updated_at"])

    with pytest.raises(TelemedicineInvitationExpiredError):
        exchange_patient_invitation(raw_token=raw_token)


def test_dashboard_serializer_never_exposes_tokens_or_provider_secrets():
    therapist, organization, _, _, room = create_context()
    client = authenticated_client(
        therapist=therapist,
        organization=organization,
    )
    create_patient_invitation(actor=therapist, room=room)

    response = client.get(reverse("telemedicine-list"))

    assert response.status_code == status.HTTP_200_OK
    serialized = json.dumps(response.data)
    for forbidden in [
        "patient_token",
        "professional_token",
        "provider_room_name",
        "provider_room_sid",
        "e2ee_key",
        "invitation_url",
    ]:
        assert forbidden not in serialized


def test_public_exchange_is_no_store_and_minimized():
    therapist, _, _, _, room = create_context()
    _, raw_token, _ = create_patient_invitation(actor=therapist, room=room)
    client = APIClient()

    response = client.post(
        reverse("telemedicine-public-exchange"),
        {"token": raw_token},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response["Cache-Control"].startswith("no-store")
    assert response["Referrer-Policy"] == "no-referrer"
    for forbidden in ["patient_name", "cpf", "phone", "email", "notes"]:
        assert forbidden not in response.data


def test_another_tenant_cannot_list_room():
    therapist_a, organization_a, _, _, room_a = create_context(suffix="tenant-a")
    therapist_b, organization_b, _, _, room_b = create_context(suffix="tenant-b")
    client = authenticated_client(
        therapist=therapist_a,
        organization=organization_a,
    )

    response = client.get(reverse("telemedicine-list"))
    ids = {item["id"] for item in response.data["results"]}

    assert room_a.pk in ids
    assert room_b.pk not in ids
    assert therapist_b.pk != therapist_a.pk
    assert organization_b.pk != organization_a.pk


def test_plan_without_telemedicine_blocks_invitation():
    therapist, _, _, _, room = create_context(
        suffix="sem-recurso",
        telemedicine_plan=False,
    )

    with pytest.raises(TelemedicineAccessDeniedError) as captured:
        create_patient_invitation(actor=therapist, room=room)

    assert "plano atual" in str(captured.value).lower()


def test_fake_webhook_is_idempotent_and_tracks_presence():
    therapist, _, _, _, room = create_context(suffix="webhook")
    _, raw_token, _ = create_patient_invitation(actor=therapist, room=room)
    record_telemedicine_consent(raw_token=raw_token, accepted=True)
    credentials = issue_patient_join_credentials(raw_token=raw_token)

    payload = json.dumps(
        {
            "id": "evt-patient-joined-1",
            "event": "participant_joined",
            "room_name": room.provider_room_name,
            "room_sid": "RM_TEST",
            "participant_identity": credentials["identity"],
            "participant_sid": "PA_TEST",
            "occurred_at": timezone.now().isoformat(),
        }
    )
    first_event, first_processed = process_telemedicine_webhook(
        raw_body=payload,
        authorization="ignored-by-fake-provider",
    )
    second_event, second_processed = process_telemedicine_webhook(
        raw_body=payload,
        authorization="ignored-by-fake-provider",
    )

    assert first_processed is True
    assert second_processed is False
    assert first_event.pk == second_event.pk
    assert TelemedicineWebhookEvent.objects.count() == 1
    assert TelemedicineParticipantSession.objects.filter(
        room=room,
        role=TelemedicineParticipantSession.Role.PATIENT,
        left_at__isnull=True,
    ).count() == 1
    assert TelemedicineConsent.objects.filter(room=room).count() == 1
