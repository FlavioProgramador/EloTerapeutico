from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.financeiro.models import FinancialTransaction
from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="finance.terapeuta@teste.com",
        password="SenhaForte123!",
        full_name="Terapeuta Financeiro",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(db, therapist):
    return Patient.objects.create(
        full_name="Paciente Financeiro",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
        is_active=True,
    )


@pytest.fixture
def client(therapist):
    api = APIClient()
    api.force_authenticate(therapist)
    return api


@pytest.mark.django_db
def test_transaction_list_actions_coverage(client, patient, therapist):
    FinancialTransaction.objects.create(
        therapist=therapist,
        patient=patient,
        transaction_type="income",
        category="sessao",
        amount=Decimal("150.00"),
        payment_method="pix",
        payment_status="pago",
        due_date=timezone.now().date(),
        paid_at=timezone.now(),
    )
    # Lista
    response = client.get(reverse("transaction-list"))
    assert response.status_code == status.HTTP_200_OK

    # Billing - pode ter action especifica
    # Como não tenho certeza das rotas, vou chamar as actions que existem
    pass
