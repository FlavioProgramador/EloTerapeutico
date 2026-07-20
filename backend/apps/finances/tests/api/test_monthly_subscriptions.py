from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.finances.models import MonthlySubscription
from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def subscription_context(db):
    user = User.objects.create_user(
        email="financeiro-mensalidade@example.com",
        full_name="Profissional Mensalidade",
        password="safe-test-password",
        role=User.Role.THERAPIST,
        crp_number="06/333333",
    )
    patient = Patient.objects.create(
        therapist=user,
        full_name="Paciente Mensalidade",
        cpf="390.533.447-05",
        birth_date=date(1992, 3, 10),
        gender="N",
        email="paciente-mensalidade@example.com",
        phone="21988888888",
        status=Patient.Status.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(user)
    return client, patient


@pytest.mark.django_db
def test_create_and_list_subscription(subscription_context):
    client, patient = subscription_context
    payload = {
        "patient": patient.pk,
        "frequency": "weekly",
        "weekday": 0,
        "appointment_time": "09:00",
        "first_appointment_date": "2026-07-06",
        "duration_minutes": 50,
        "monthly_amount": "600.00",
        "due_day": 5,
        "first_due_date": "2026-07-05",
    }
    created = client.post("/api/v1/finances/subscriptions/", payload, format="json")
    listed = client.get("/api/v1/finances/subscriptions/")
    assert created.status_code == 201
    assert listed.status_code == 200
    assert len(listed.data) == 1
    subscription = MonthlySubscription.objects.get(pk=created.data["id"])
    assert subscription.therapist == patient.therapist
    assert subscription.monthly_amount == Decimal("600.00")
    assert subscription.charges.count() == 1
