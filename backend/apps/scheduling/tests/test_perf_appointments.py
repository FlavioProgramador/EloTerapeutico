from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.extended_models import EvolutionClinicalData
from apps.records.models import Evolution
from apps.scheduling.models import Appointment
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
def test_appointment_list_optimized_queries(
    api_client,
    therapist,
    patient,
    django_assert_num_queries,
):
    """Verifica ausência de N+1 incluindo a resolução constante do tenant."""

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
        EvolutionClinicalData.objects.create(
            evolution=evo,
            status="finalized",
            updated_by=therapist,
        )

    url = reverse("appointment-list")

    # Membership ativa + Count + listagem principal. O total permanece constante,
    # mesmo com evoluções e dados clínicos relacionados.
    with django_assert_num_queries(3):
        response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == num_appointments


@pytest.mark.django_db
def test_appointment_serializer_memoizes_cached_relations(therapist, patient):
    """Garante que a serialização memoize relacionamentos evitando reavaliações."""
    from apps.scheduling.api.serializers.appointment_read import (
        AppointmentDetailSerializer,
        AppointmentListSerializer,
    )

    start = timezone.now()
    appt_without_evo = Appointment.objects.create(
        patient=patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=100,
    )

    list_serializer = AppointmentListSerializer(appt_without_evo)
    data = list_serializer.data

    assert data["evolution_id"] is None
    assert data["evolution_status"] is None
    assert data["telemedicine_status"] is None
    assert getattr(appt_without_evo, "_cached_evolution", "MISSING") is None
    assert getattr(appt_without_evo, "_cached_telemedicine_room", "MISSING") is None

    detail_serializer = AppointmentDetailSerializer(appt_without_evo)
    detail_data = detail_serializer.data
    assert detail_data["telemedicine"] is None

    # Com evolução
    appt_with_evo = Appointment.objects.create(
        patient=patient,
        therapist=therapist,
        start_time=start + timedelta(days=1),
        end_time=start + timedelta(days=1, minutes=50),
        session_value=100,
    )
    evo = Evolution.objects.create(
        patient=patient,
        appointment=appt_with_evo,
        session_date=(start + timedelta(days=1)).date(),
        created_by=therapist,
        content="Evolution test",
    )
    EvolutionClinicalData.objects.create(
        evolution=evo,
        status="finalized",
        updated_by=therapist,
    )

    list_serializer_2 = AppointmentListSerializer(appt_with_evo)
    data_2 = list_serializer_2.data
    assert data_2["evolution_id"] == evo.id
    assert data_2["evolution_status"] == "finalized"
    assert appt_with_evo._cached_evolution == evo
