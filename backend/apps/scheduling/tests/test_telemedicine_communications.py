from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.billing.models import Plan, Subscription
from apps.communications.models import Communication
from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
)
from apps.patients.models import Patient
from apps.scheduling.integrations.communications import send_telemedicine_invitation
from apps.scheduling.models import Appointment, TelemedicineInvitation, TelemedicineRoom
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def telemedicine_environment(monkeypatch, settings):
    settings.DEBUG = True
    monkeypatch.setenv("TELEMEDICINE_ENABLED", "True")
    monkeypatch.setenv("TELEMEDICINE_PROVIDER", "fake")
    monkeypatch.setenv("TELEMEDICINE_REQUIRE_E2EE", "True")


def create_context(*, suffix: str):
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
        is_default=True,
    )
    plan = Plan.objects.create(
        name=f"Plano {suffix.title()}",
        slug=f"plano-{suffix}",
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
        full_name=f"Paciente {suffix.title()}",
        email=f"paciente-{suffix}@example.test",
    )
    start = now + timedelta(hours=6)
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
    return therapist, appointment, room


def test_first_send_queues_invitation_and_schedules_reminder():
    therapist, appointment, room = create_context(suffix="lembrete")

    invitation_message = send_telemedicine_invitation(
        actor=therapist,
        room=room,
        channel=Communication.Channel.EMAIL,
    )

    reminder = Communication.objects.get(
        appointment=appointment,
        source_event="telemedicine.invitation.reminder",
    )
    assert invitation_message.status == Communication.Status.QUEUED
    assert reminder.status == Communication.Status.SCHEDULED
    assert reminder.scheduled_at == appointment.start_time - timedelta(hours=2)
    assert TelemedicineInvitation.objects.filter(
        room=room,
        revoked_at__isnull=True,
    ).count() == 1


def test_reschedule_replaces_invitation_and_reschedules_reminder(
    django_capture_on_commit_callbacks,
):
    therapist, appointment, room = create_context(suffix="reagendamento")
    send_telemedicine_invitation(actor=therapist, room=room)
    first_invitation = TelemedicineInvitation.objects.get(
        room=room,
        revoked_at__isnull=True,
    )

    appointment.start_time += timedelta(days=1)
    appointment.end_time += timedelta(days=1)
    with django_capture_on_commit_callbacks(execute=True):
        appointment.save(update_fields=["start_time", "end_time", "updated_at"])

    first_invitation.refresh_from_db()
    active_invitation = TelemedicineInvitation.objects.get(
        room=room,
        revoked_at__isnull=True,
    )
    active_reminder = Communication.objects.get(
        appointment=appointment,
        source_event="telemedicine.invitation.reminder",
        status=Communication.Status.SCHEDULED,
    )

    assert first_invitation.revoked_at is not None
    assert active_invitation.pk != first_invitation.pk
    assert active_reminder.scheduled_at == appointment.start_time - timedelta(hours=2)
    assert Communication.objects.filter(
        appointment=appointment,
        source_event="telemedicine.invitation.reminder",
        status=Communication.Status.CANCELED,
    ).exists()


def test_cancellation_revokes_access_and_queues_notice(
    django_capture_on_commit_callbacks,
):
    therapist, appointment, room = create_context(suffix="cancelamento")
    send_telemedicine_invitation(actor=therapist, room=room)

    appointment.status = Appointment.Status.CANCELLED
    with django_capture_on_commit_callbacks(execute=True):
        appointment.save(update_fields=["status", "updated_at"])

    room.refresh_from_db()
    assert room.status == TelemedicineRoom.Status.CANCELLED
    assert room.revoked_at is not None
    assert not TelemedicineInvitation.objects.filter(
        room=room,
        revoked_at__isnull=True,
    ).exists()
    assert Communication.objects.filter(
        appointment=appointment,
        source_event="telemedicine.appointment.canceled",
        status=Communication.Status.QUEUED,
    ).exists()
    assert not Communication.objects.filter(
        appointment=appointment,
        source_event="telemedicine.invitation.reminder",
        status=Communication.Status.SCHEDULED,
    ).exists()
