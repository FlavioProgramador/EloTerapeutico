from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.agenda.models import Appointment
from apps.patients.models import Patient
from apps.records.extended_models import EvolutionClinicalData
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="perf.therapist@example.com",
        password="password123",
        role=User.Role.THERAPIST,
        full_name="Perf Therapist",
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(full_name="Perf Patient", therapist=therapist)


@pytest.fixture
def api_client(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    return client


@pytest.mark.django_db
def test_appointment_list_optimized_queries(api_client, therapist, patient, django_assert_num_queries):
    """
    Verifica que a listagem de agendamentos não possui N+1 queries para evoluções.
    """
    num_appointments = 5
    for i in range(num_appointments):
        start = timezone.now() + timedelta(days=i)
        appt = Appointment.objects.create(
            patient=patient,
            therapist=therapist,
            start_time=start,
            end_time=start + timedelta(minutes=50),
            session_value=100,
        )
        evo = Evolution.objects.create(
            patient=patient,
            appointment=appt,
            session_date=start.date(),
            created_by=therapist,
            content=f"Evolution {i}",
        )
        EvolutionClinicalData.objects.create(evolution=evo, status="finalized", updated_by=therapist)

    url = reverse("appointment-list")

    # Com a otimização select_related('evolution', 'evolution__clinical_data')
    # e remoção de prefetches desnecessários (participants, reminders),
    # o número total de queries caiu de 4 para 2 (Count + Main List).
    # (O User é autenticado via force_authenticate e não gera query se já carregado no fixture).
    with django_assert_num_queries(2):
        response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == num_appointments
