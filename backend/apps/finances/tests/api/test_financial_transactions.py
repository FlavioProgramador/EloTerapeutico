"""
Testes de integridade, transições de status e isolamento de dados do módulo Financeiro.
"""

import csv
import io
from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.test import APIClient

from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.scheduling.models import Appointment
from apps.users.models import User


@pytest.fixture
def other_therapist(db):
    return User.objects.create_user(
        email="outro_terapeuta@teste.com",
        full_name="Dr. Outro Terapeuta",
        password=get_random_string(length=16),
        role=User.Role.THERAPIST,
        crp_number="06/654321",
    )


@pytest.fixture
def auth_client(therapist_user):
    client = APIClient()
    client.force_authenticate(user=therapist_user)
    return client


@pytest.fixture
def auth_other_client(other_therapist):
    client = APIClient()
    client.force_authenticate(user=other_therapist)
    return client


@pytest.fixture
def patient_of_therapist(db, therapist_user):
    return Patient.objects.create(
        full_name="Paciente Principal",
        cpf="123.456.789-01",
        birth_date=date(1990, 1, 1),
        gender="M",
        email="principal@teste.com",
        phone="11999999999",
        therapist=therapist_user,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def patient_of_other_therapist(db, other_therapist):
    return Patient.objects.create(
        full_name="Paciente do Outro",
        cpf="987.654.321-09",
        birth_date=date(1995, 5, 5),
        gender="F",
        email="outro_paciente@teste.com",
        phone="11988887777",
        therapist=other_therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def appointment_of_therapist(db, therapist_user, patient_of_therapist):
    now = timezone.now()
    return Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        status=Appointment.Status.SCHEDULED,
        session_value=150.00,
    )


@pytest.fixture
def appointment_of_other_therapist(db, other_therapist, patient_of_other_therapist):
    now = timezone.now()
    return Appointment.objects.create(
        therapist=other_therapist,
        patient=patient_of_other_therapist,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        status=Appointment.Status.SCHEDULED,
        session_value=180.00,
    )


@pytest.mark.django_db
def test_create_transaction_success(auth_client, patient_of_therapist, appointment_of_therapist):
    url = reverse("transaction-list")
    payload = {
        "transaction_type": "income",
        "category": "session",
        "amount": "150.00",
        "payment_method": "pix",
        "payment_status": "pending",
        "due_date": str(date.today()),
        "patient": patient_of_therapist.id,
        "appointment": appointment_of_therapist.id,
        "description": "Sessão teste",
    }
    response = auth_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["transaction_type"] == "income"
    assert response.data["amount"] == "150.00"
    tx = FinancialTransaction.objects.get(id=response.data["id"])
    assert tx.therapist.email == "terapeuta@teste.com"


@pytest.mark.django_db
def test_create_transaction_therapist_override(auth_client, other_therapist):
    url = reverse("transaction-list")
    payload = {
        "transaction_type": "expense",
        "category": "material",
        "amount": "80.00",
        "payment_method": "cash",
        "payment_status": "paid",
        "due_date": str(date.today()),
        "therapist": other_therapist.id,
        "description": "Material de limpeza",
    }
    response = auth_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    tx = FinancialTransaction.objects.get(id=response.data["id"])
    assert tx.therapist.email == "terapeuta@teste.com"


@pytest.mark.django_db
def test_create_transaction_other_patient_validation(auth_client, patient_of_other_therapist):
    response = auth_client.post(
        reverse("transaction-list"),
        {"transaction_type": "income", "category": "session", "amount": "120.00", "patient": patient_of_other_therapist.id},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "patient" in response.data["error"]["details"]


@pytest.mark.django_db
def test_create_transaction_other_appointment_validation(auth_client, appointment_of_other_therapist):
    response = auth_client.post(
        reverse("transaction-list"),
        {"transaction_type": "income", "category": "session", "amount": "120.00", "appointment": appointment_of_other_therapist.id},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "appointment" in response.data["error"]["details"]


@pytest.mark.django_db
def test_transaction_pay_flow(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )
    response = auth_client.patch(reverse("transaction-mark-as-paid", args=[tx.id]), {"payment_method": "credit_card"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["payment_status"] == "paid"
    assert response.data["payment_method"] == "credit_card"
    tx.refresh_from_db()
    assert tx.payment_status == FinancialTransaction.PaymentStatus.PAID
    assert tx.paid_at is not None


@pytest.mark.django_db
def test_transaction_pay_already_paid_error(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )
    assert auth_client.patch(reverse("transaction-mark-as-paid", args=[tx.id]), {}, format="json").status_code == 400


@pytest.mark.django_db
def test_transaction_cancel_success(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )
    response = auth_client.post(reverse("transaction-cancel", args=[tx.id]), {}, format="json")
    assert response.status_code == 200
    assert response.data["payment_status"] == "cancelled"


@pytest.mark.django_db
def test_transaction_cancel_invalid_state(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )
    assert auth_client.post(reverse("transaction-cancel", args=[tx.id]), {}, format="json").status_code == 400


@pytest.mark.django_db
def test_transaction_refund_success(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )
    response = auth_client.post(reverse("transaction-refund", args=[tx.id]), {}, format="json")
    assert response.status_code == 200
    assert response.data["payment_status"] == "refunded"


@pytest.mark.django_db
def test_transaction_refund_invalid_state(auth_client, therapist_user):
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )
    assert auth_client.post(reverse("transaction-refund", args=[tx.id]), {}, format="json").status_code == 400


@pytest.mark.django_db
def test_transaction_list_isolation(auth_client, auth_other_client, therapist_user, other_therapist):
    FinancialTransaction.objects.create(therapist=therapist_user, transaction_type="income", amount=100.00, payment_status="paid")
    FinancialTransaction.objects.create(therapist=other_therapist, transaction_type="expense", amount=200.00, payment_status="paid")
    res1 = auth_client.get(reverse("transaction-list"))
    results1 = res1.data.get("results", res1.data)
    assert len(results1) == 1 and results1[0]["amount"] == "100.00"
    res2 = auth_other_client.get(reverse("transaction-list"))
    results2 = res2.data.get("results", res2.data)
    assert len(results2) == 1 and results2[0]["amount"] == "200.00"


@pytest.mark.django_db
def test_transaction_detail_isolation(auth_client, other_therapist):
    tx = FinancialTransaction.objects.create(therapist=other_therapist, transaction_type="income", amount=100.00, payment_status="paid")
    assert auth_client.get(reverse("transaction-detail", args=[tx.id])).status_code == 404


@pytest.mark.django_db
def test_export_csv_success(auth_client, therapist_user):
    FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type="income",
        category="session",
        amount=150.00,
        payment_status="paid",
        description="=Sessão clínica",
    )
    response = auth_client.get(reverse("transaction-export-csv"))
    assert response.status_code == 200
    csv_file = io.StringIO(response.content.decode("utf-8-sig"))
    rows = list(csv.reader(csv_file, delimiter=";"))
    assert len(rows) == 2
    assert rows[1][9] == "'=Sessão clínica"


@pytest.mark.django_db
def test_unbilled_appointments_listing(auth_client, therapist_user, patient_of_therapist, other_therapist, patient_of_other_therapist):
    now = timezone.now()
    appt1 = Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=Appointment.Status.CONFIRMED,
        session_value=120.00,
    )
    appt2 = Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now - timedelta(days=1),
        end_time=now - timedelta(days=1, hours=-1),
        status=Appointment.Status.CONFIRMED,
        session_value=120.00,
    )
    FinancialTransaction.objects.create(therapist=therapist_user, appointment=appt2, amount=120.00, payment_status="paid")
    Appointment.objects.create(
        therapist=other_therapist,
        patient=patient_of_other_therapist,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=Appointment.Status.CONFIRMED,
        session_value=150.00,
    )
    response = auth_client.get(reverse("transaction-unbilled-appointments"))
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == appt1.id
