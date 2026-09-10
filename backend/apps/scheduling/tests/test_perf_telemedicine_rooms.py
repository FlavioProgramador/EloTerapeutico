from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan, Subscription
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
)
from apps.patients.models import Patient
from apps.scheduling.api.v1.serializers import TelemedicineRoomSerializer
from apps.scheduling.models import (
    Appointment,
    TelemedicineParticipantSession,
    TelemedicineRoom,
)
from apps.scheduling.selectors.resources import telemedicine_rooms_queryset
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def telemedicine_environment(monkeypatch, settings):
    settings.DEBUG = True
    monkeypatch.setenv("TELEMEDICINE_ENABLED", "True")
    monkeypatch.setenv("TELEMEDICINE_PROVIDER", "fake")


def create_perf_telemedicine_setup(num_rooms: int = 5):
    therapist = User.objects.create_user(
        email="perf-telemed@example.test",
        full_name="Perf Telemed Therapist",
        password="TestPass2026!",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Clínica Telemed Perf",
        slug="clinica-telemed-perf",
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
        name="Plano Telemed Perf",
        slug="plano-telemed-perf",
        price=Decimal("99.00"),
        has_telemedicine=True,
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
        full_name="Paciente Telemed Perf",
    )

    rooms = []
    for i in range(num_rooms):
        start = now + timedelta(minutes=5 + i * 60)
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
        TelemedicineParticipantSession.objects.create(
            organization=organization,
            room=room,
            role=TelemedicineParticipantSession.Role.PATIENT,
            provider_participant_identity=f"identity_{i}",
            joined_at=now,
        )
        rooms.append(room)

    return therapist, organization, rooms


def test_telemedicine_room_serializer_active_participants_query_count(django_assert_num_queries):
    _, _, rooms = create_perf_telemedicine_setup(num_rooms=5)

    # 1query para TelemedicineRoom (select_related) + 1 para invitations (prefetch) + 1 para participant_sessions (prefetch)
    with django_assert_num_queries(3):
        qs = telemedicine_rooms_queryset().filter(id__in=[r.id for r in rooms])
        serialized = TelemedicineRoomSerializer(qs, many=True).data
        assert len(serialized) == 5
        for item in serialized:
            assert len(item["active_participants"]) == 1
            assert item["active_participants"][0]["role"] == "patient"
