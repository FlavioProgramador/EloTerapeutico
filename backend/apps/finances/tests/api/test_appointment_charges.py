from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.scheduling.models import Appointment
from apps.users.models import User


@pytest.fixture
def billing_context(db):
    user = User.objects.create_user(
        email="financeiro-cobranca@example.com",
        full_name="Profissional Cobrança",
        password="safe-test-password",
        role=User.Role.THERAPIST,
        crp_number="06/222222",
    )
    patient = Patient.objects.create(
        therapist=user,
        full_name="Paciente Fictício",
        cpf="529.982.247-25",
        birth_date=date(1990, 1, 1),
        gender="N",
        email="paciente-cobranca@example.com",
        phone="21999999999",
        status=Patient.Status.ACTIVE,
    )
    start = timezone.now() - timedelta(days=1)
    appointment = Appointment.objects.create(
        therapist=user,
        patient=patient,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        status=Appointment.Status.COMPLETED,
        session_value=Decimal("180.00"),
    )
    client = APIClient()
    client.force_authenticate(user)
    return client, appointment


@pytest.mark.django_db
def test_batch_billing_is_idempotent(billing_context):
    client, appointment = billing_context
    payload = {"appointment_ids": [appointment.pk], "due_date": "2026-07-15"}

    first = client.post("/api/v1/finances/generate-monthly-charges/", payload, format="json")
    second = client.post("/api/v1/finances/generate-monthly-charges/", payload, format="json")

    assert first.status_code == 201
    assert first.data["created_count"] == 1
    assert second.status_code == 201
    assert second.data["created_count"] == 0
    assert second.data["skipped"] == [appointment.pk]
    assert FinancialTransaction.objects.filter(appointment=appointment).count() == 1


@pytest.mark.django_db
def test_batch_billing_rejects_unknown_appointment(billing_context):
    client, _ = billing_context
    response = client.post(
        "/api/v1/finances/generate-monthly-charges/",
        {"appointment_ids": [999999], "due_date": "2026-07-15"},
        format="json",
    )
    assert response.status_code == 400
