from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def listing_users(db):
    therapist = User.objects.create_user(
        email="listing-therapist@example.com",
        password="safe-password",
        full_name="Terapeuta Listagem",
        role=User.Role.THERAPIST,
    )
    secretary = User.objects.create_user(
        email="listing-secretary@example.com",
        password="safe-password",
        full_name="Secretária Listagem",
        role=User.Role.SECRETARY,
    )
    other = User.objects.create_user(
        email="listing-other@example.com",
        password="safe-password",
        full_name="Outro Terapeuta",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente da Listagem",
        cpf="52998224725",
        birth_date=date(1994, 5, 10),
        therapist=therapist,
        reminders_enabled=True,
    )
    foreign = Patient.objects.create(
        full_name="Paciente Estrangeiro",
        cpf="11144477735",
        birth_date=date(1988, 3, 15),
        therapist=other,
    )
    return therapist, secretary, patient, foreign


@pytest.mark.django_db
def test_listagem_expoe_lembrete_sem_expor_cpf(listing_users):
    therapist, _, patient, foreign = listing_users
    client = APIClient()
    client.force_authenticate(therapist)

    response = client.get(reverse("patient-list"))

    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert patient.id in ids
    assert foreign.id not in ids
    item = next(item for item in response.data["results"] if item["id"] == patient.id)
    assert item["reminders_enabled"] is True
    assert item["masked_cpf"] == "529.***.***-25"
    assert "cpf" not in item


@pytest.mark.django_db
def test_terapeuta_altera_lembrete_do_proprio_paciente(listing_users):
    therapist, _, patient, _ = listing_users
    client = APIClient()
    client.force_authenticate(therapist)

    response = client.patch(
        reverse("patient-reminders", kwargs={"pk": patient.id}),
        {"enabled": False},
        format="json",
    )

    assert response.status_code == 200
    patient.refresh_from_db()
    assert patient.reminders_enabled is False


@pytest.mark.django_db
def test_secretaria_nao_altera_lembrete(listing_users):
    _, secretary, patient, _ = listing_users
    client = APIClient()
    client.force_authenticate(secretary)

    response = client.patch(
        reverse("patient-reminders", kwargs={"pk": patient.id}),
        {"enabled": False},
        format="json",
    )

    assert response.status_code == 403
    patient.refresh_from_db()
    assert patient.reminders_enabled is True


@pytest.mark.django_db
def test_terapeuta_nao_altera_lembrete_de_outro_profissional(listing_users):
    therapist, _, _, foreign = listing_users
    client = APIClient()
    client.force_authenticate(therapist)

    response = client.patch(
        reverse("patient-reminders", kwargs={"pk": foreign.id}),
        {"enabled": False},
        format="json",
    )

    assert response.status_code == 404
