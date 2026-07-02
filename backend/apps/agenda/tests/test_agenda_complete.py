"""Cobertura principal do módulo completo de Agenda."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.users.models import User
from ..models import (
    Appointment,
    AppointmentRecurrence,
    PatientPackage,
    Room,
    ScheduleBlock,
    TelemedicineRoom,
)


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="agenda.terapeuta@teste.com",
        password="SenhaForte123!",
        full_name="Terapeuta Agenda",
        role=User.Role.THERAPIST,
        default_session_value=Decimal("150.00"),
    )


@pytest.fixture
def other_therapist(db):
    return User.objects.create_user(
        email="agenda.outro@teste.com",
        password="SenhaForte123!",
        full_name="Outro Terapeuta",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(db, therapist):
    return Patient.objects.create(
        full_name="Paciente Agenda",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
        is_active=True,
        session_value=Decimal("150.00"),
    )


@pytest.fixture
def other_patient(db, other_therapist):
    return Patient.objects.create(
        full_name="Paciente Externo",
        therapist=other_therapist,
        status=Patient.Status.ACTIVE,
        is_active=True,
    )


@pytest.fixture
def client(therapist):
    api = APIClient()
    api.force_authenticate(therapist)
    return api


def appointment_payload(patient, start=None, **overrides):
    start = start or timezone.now() + timedelta(days=2)
    payload = {
        "patient": patient.id,
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(minutes=50)).isoformat(),
        "modality": "in_person",
        "appointment_type": "psychotherapy",
        "session_value": "150.00",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_create_appointment(client, patient):
    response = client.post(
        reverse("appointment-list"), appointment_payload(patient), format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    appointment = Appointment.objects.get(pk=response.data["id"])
    assert appointment.patient == patient
    assert appointment.therapist == patient.therapist


@pytest.mark.django_db
def test_blocks_therapist_overlap(client, patient):
    start = timezone.now() + timedelta(days=3)
    Appointment.objects.create(
        patient=patient,
        therapist=patient.therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, start=start + timedelta(minutes=10)),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_blocks_patient_overlap_with_other_professional(
    client, patient, other_therapist
):
    start = timezone.now() + timedelta(days=4)
    Appointment.objects.create(
        patient=patient,
        therapist=other_therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, start=start),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_blocks_room_overlap(client, patient, other_patient, therapist):
    room = Room.objects.create(therapist=therapist, name="Sala 1")
    start = timezone.now() + timedelta(days=5)
    Appointment.objects.create(
        patient=other_patient,
        therapist=therapist,
        room=room,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, start=start, room=room.id),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_schedule_block_prevents_appointment(client, patient, therapist):
    start = timezone.now() + timedelta(days=6)
    ScheduleBlock.objects.create(
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(hours=2),
        reason=ScheduleBlock.Reason.MEETING,
    )
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, start=start),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_recurring_appointment_materializes_series(client, patient):
    start = timezone.now() + timedelta(days=8)
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(
            patient,
            start=start,
            is_recurring=True,
            recurrence_frequency="weekly",
            recurrence_max_occurrences=4,
        ),
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    recurrence = AppointmentRecurrence.objects.get()
    assert recurrence.appointments.count() == 4


@pytest.mark.django_db
def test_package_balance_never_becomes_negative(client, patient, therapist):
    package = PatientPackage.objects.create(
        patient=patient,
        therapist=therapist,
        name="Pacote 1",
        sessions_contracted=1,
        total_value=150,
    )
    first = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, package=package.id),
        format="json",
    )
    assert first.status_code == status.HTTP_201_CREATED
    second = client.post(
        reverse("appointment-list"),
        appointment_payload(
            patient,
            start=timezone.now() + timedelta(days=20),
            package=package.id,
        ),
        format="json",
    )
    assert second.status_code == status.HTTP_400_BAD_REQUEST
    package.refresh_from_db()
    assert package.sessions_used == 1
    assert package.remaining_sessions == 0


@pytest.mark.django_db
def test_online_appointment_creates_secure_room(client, patient):
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, modality="online"),
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    room = TelemedicineRoom.objects.get(appointment_id=response.data["id"])
    assert room.patient_token != room.professional_token
    assert room.is_accessible


@pytest.mark.django_db
def test_therapist_cannot_use_another_professionals_patient(
    client, other_patient
):
    response = client.post(
        reverse("appointment-list"),
        appointment_payload(other_patient),
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_queryset_isolated_by_professional(
    client, patient, other_patient, other_therapist
):
    own_start = timezone.now() + timedelta(days=30)
    own = Appointment.objects.create(
        patient=patient,
        therapist=patient.therapist,
        start_time=own_start,
        end_time=own_start + timedelta(minutes=50),
        session_value=150,
    )
    other_start = timezone.now() + timedelta(days=31)
    Appointment.objects.create(
        patient=other_patient,
        therapist=other_therapist,
        start_time=other_start,
        end_time=other_start + timedelta(minutes=50),
        session_value=150,
    )
    response = client.get(reverse("appointment-list"))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.data["results"]}
    assert ids == {own.id}


@pytest.mark.django_db
def test_block_requires_confirmation_when_consultations_are_affected(
    client, patient, therapist
):
    start = timezone.now() + timedelta(days=40)
    Appointment.objects.create(
        patient=patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )
    payload = {
        "therapist": therapist.id,
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=1)).isoformat(),
        "reason": "meeting",
    }
    response = client.post(
        reverse("schedule-block-list"), payload, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    payload["confirm_conflicts"] = True
    response = client.post(
        reverse("schedule-block-list"), payload, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_cancel_releases_package_balance(client, patient, therapist):
    package = PatientPackage.objects.create(
        patient=patient,
        therapist=therapist,
        name="Pacote cancelamento",
        sessions_contracted=2,
        total_value=300,
    )
    created = client.post(
        reverse("appointment-list"),
        appointment_payload(patient, package=package.id),
        format="json",
    )
    assert created.status_code == status.HTTP_201_CREATED
    response = client.post(
        reverse("appointment-cancel", args=[created.data["id"]]),
        {"cancellation_reason": "Solicitação do paciente"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    package.refresh_from_db()
    assert package.sessions_used == 0
