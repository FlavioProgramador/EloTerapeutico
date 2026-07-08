import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.users.models import User
from apps.patients.models import Patient
from apps.agenda.models import TelemedicineRoom, Appointment

@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="tele.terapeuta@teste.com",
        password="SenhaForte123!",
        full_name="Terapeuta Tele",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def patient(db, therapist):
    return Patient.objects.create(
        full_name="Paciente Tele",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
        is_active=True,
    )

@pytest.fixture
def client(therapist):
    api = APIClient()
    api.force_authenticate(therapist)
    return api

@pytest.fixture
def appointment(patient, therapist):
    start = timezone.now() + timedelta(days=2)
    return Appointment.objects.create(
        patient=patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        modality="online",
        session_value=150,
    )

@pytest.mark.django_db
def test_telemedicine_room_list(client, appointment):
    TelemedicineRoom.objects.create(
        appointment=appointment,
        patient_token=uuid.uuid4(),
        professional_token=uuid.uuid4(),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    response = client.get(reverse("telemedicine-list"))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) >= 1

@pytest.mark.django_db
def test_telemedicine_access_view(appointment):
    api = APIClient()
    room = TelemedicineRoom.objects.create(
        appointment=appointment,
        patient_token=uuid.uuid4(),
        professional_token=uuid.uuid4(),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    # Token do paciente
    response = api.get(reverse("telemedicine-access", args=["patient", room.patient_token]))
    assert response.status_code == status.HTTP_200_OK
    assert "patient_name" in response.data

    # Token invalido
    bad_response = api.get(reverse("telemedicine-access", args=["patient", uuid.uuid4()]))
    assert bad_response.status_code == status.HTTP_404_NOT_FOUND
