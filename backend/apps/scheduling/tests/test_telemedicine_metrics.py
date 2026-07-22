from __future__ import annotations

import json

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.scheduling.models import (
    TelemedicineInvitation,
    TelemedicineParticipantSession,
    TelemedicineWebhookEvent,
)
from apps.scheduling.tests.test_telemedicine_communications import create_context

pytestmark = pytest.mark.django_db


def add_operational_events(room):
    TelemedicineInvitation.objects.create(
        organization=room.organization,
        room=room,
        token_hash=room.public_id.hex * 2,
        expires_at=room.expires_at,
        last_used_at=timezone.now(),
    )
    TelemedicineParticipantSession.objects.create(
        organization=room.organization,
        room=room,
        role=TelemedicineParticipantSession.Role.PATIENT,
        provider_participant_identity=f"telemed:{room.public_id.hex}:patient:test",
        connection_aborted=True,
    )
    TelemedicineWebhookEvent.objects.create(
        provider="livekit",
        provider_event_id=f"evt-{room.public_id.hex}",
        event_type="participant_joined",
        room=room,
        payload_hash="b" * 64,
        processed_at=timezone.now(),
    )


def test_operational_metrics_are_tenant_scoped_and_do_not_expose_pii():
    therapist, appointment, room = create_context(suffix="metricas-a")
    _, other_appointment, other_room = create_context(suffix="metricas-b")
    add_operational_events(room)
    add_operational_events(other_room)

    client = APIClient()
    client.force_authenticate(therapist)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(room.organization_id))
    response = client.get(reverse("telemedicine-operational-metrics"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["rooms"]["total"] == 1
    assert response.data["participants"]["active"] == 1
    assert response.data["participants"]["aborted_in_window"] == 1
    assert response.data["invitations"]["used_in_window"] == 1
    assert response.data["webhooks"]["received_in_window"] == 1

    serialized = json.dumps(response.data, default=str)
    for forbidden in [
        appointment.patient.full_name,
        appointment.patient.email,
        str(room.public_id),
        other_appointment.patient.full_name,
        other_appointment.patient.email,
        str(other_room.public_id),
        "token_hash",
        "provider_room_name",
    ]:
        assert forbidden not in serialized
