from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.records.extended_models import EvolutionClinicalData
from apps.records.models import Evolution
from apps.scheduling.models import Appointment, AppointmentRecurrence
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
def test_recurrence_list_optimized_queries(
    api_client,
    therapist,
    patient,
    django_assert_num_queries,
):
    """Verifica ausência de N+1 na listagem de recorrências."""
    membership = OrganizationMembership.objects.get(user=therapist)
    organization = membership.organization
    patient.organization = organization
    patient.save(update_fields=["organization"])

    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))

    num_recurrences = 5
    for i in range(num_recurrences):
        rec = AppointmentRecurrence.objects.create(
            organization=organization,
            patient=patient,
            therapist=therapist,
            frequency=AppointmentRecurrence.Frequency.WEEKLY,
            starts_on=timezone.now().date(),
            start_time=timezone.now().time(),
            duration_minutes=50,
        )
        for j in range(3):
            Appointment.objects.create(
                organization=organization,
                patient=patient,
                therapist=therapist,
                recurrence=rec,
                start_time=timezone.now() + timedelta(days=i * 7 + j),
                end_time=timezone.now() + timedelta(days=i * 7 + j, minutes=50),
                session_value=100,
                status=Appointment.Status.SCHEDULED if j > 0 else Appointment.Status.CONFIRMED,
            )

    url = reverse("appointment-recurrence-list")

    # Sem N+1, as consultas para resolver a listagem são fixas (O(1)).
    with django_assert_num_queries(4):
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == num_recurrences
