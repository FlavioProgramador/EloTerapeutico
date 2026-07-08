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

from apps.agenda.models import Appointment
from apps.financeiro.models import FinancialTransaction
from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def other_therapist(db):
    """Outro terapeuta para testes de isolamento."""
    return User.objects.create_user(
        email="outro_terapeuta@teste.com",
        full_name="Dr. Outro Terapeuta",
        password=get_random_string(length=16),
        role=User.Role.THERAPIST,
        crp_number="06/654321",
    )


@pytest.fixture
def auth_client(therapist_user):
    """APIClient autenticado como terapeuta principal (instância isolada)."""
    client = APIClient()
    client.force_authenticate(user=therapist_user)
    return client


@pytest.fixture
def auth_other_client(other_therapist):
    """APIClient autenticado como o outro terapeuta (instância isolada)."""
    client = APIClient()
    client.force_authenticate(user=other_therapist)
    return client


@pytest.fixture
def patient_of_therapist(db, therapist_user):
    """Paciente associado ao terapeuta logado."""
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
    """Paciente associado ao outro terapeuta."""
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
    """Consulta associada ao terapeuta logado."""
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
    """Consulta associada ao outro terapeuta."""
    now = timezone.now()
    return Appointment.objects.create(
        therapist=other_therapist,
        patient=patient_of_other_therapist,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        status=Appointment.Status.SCHEDULED,
        session_value=180.00,
    )


# ── Testes de Criação e Edição ───────────────────────────────────────────────


@pytest.mark.django_db
def test_create_transaction_success(auth_client, patient_of_therapist, appointment_of_therapist):
    """Garante que a transação é criada com sucesso associada ao terapeuta logado."""
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

    # Valida no banco
    tx = FinancialTransaction.objects.get(id=response.data["id"])
    assert tx.therapist.email == "terapeuta@teste.com"


@pytest.mark.django_db
def test_create_transaction_therapist_override(auth_client, other_therapist):
    """Garante que o backend ignora qualquer therapist enviado no payload e associa ao logado."""
    url = reverse("transaction-list")
    payload = {
        "transaction_type": "expense",
        "category": "material",
        "amount": "80.00",
        "payment_method": "cash",
        "payment_status": "paid",
        "due_date": str(date.today()),
        "therapist": other_therapist.id,  # Tentativa de associar a outro terapeuta
        "description": "Material de limpeza",
    }
    response = auth_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    tx = FinancialTransaction.objects.get(id=response.data["id"])
    assert tx.therapist.email == "terapeuta@teste.com"  # Deve ser o usuário logado


@pytest.mark.django_db
def test_create_transaction_other_patient_validation(auth_client, patient_of_other_therapist):
    """Impede a criação de transação vinculada a paciente de outro terapeuta."""
    url = reverse("transaction-list")
    payload = {
        "transaction_type": "income",
        "category": "session",
        "amount": "120.00",
        "patient": patient_of_other_therapist.id,
    }
    response = auth_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "patient" in response.data["error"]["details"]


@pytest.mark.django_db
def test_create_transaction_other_appointment_validation(auth_client, appointment_of_other_therapist):
    """Impede a criação de transação vinculada a consulta de outro terapeuta."""
    url = reverse("transaction-list")
    payload = {
        "transaction_type": "income",
        "category": "session",
        "amount": "120.00",
        "appointment": appointment_of_other_therapist.id,
    }
    response = auth_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "appointment" in response.data["error"]["details"]


# ── Testes de Transições de Status (Negócio) ──────────────────────────────────


@pytest.mark.django_db
def test_transaction_pay_flow(auth_client, therapist_user):
    """Garante transição válida de PENDING -> PAID."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )

    url = reverse("transaction-mark-as-paid", args=[tx.id])
    payload = {"payment_method": "credit_card"}
    response = auth_client.patch(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["payment_status"] == "paid"
    assert response.data["payment_method"] == "credit_card"

    tx.refresh_from_db()
    assert tx.payment_status == FinancialTransaction.PaymentStatus.PAID
    assert tx.payment_method == "credit_card"
    assert tx.paid_at is not None


@pytest.mark.django_db
def test_transaction_pay_already_paid_error(auth_client, therapist_user):
    """Impede pagar uma transação que já está paga."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )

    url = reverse("transaction-mark-as-paid", args=[tx.id])
    response = auth_client.patch(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_transaction_cancel_success(auth_client, therapist_user):
    """Garante transição válida de PENDING -> CANCELLED."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )

    url = reverse("transaction-cancel", args=[tx.id])
    response = auth_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["payment_status"] == "cancelled"

    tx.refresh_from_db()
    assert tx.payment_status == FinancialTransaction.PaymentStatus.CANCELLED


@pytest.mark.django_db
def test_transaction_cancel_invalid_state(auth_client, therapist_user):
    """Impede cancelar uma transação já paga."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )

    url = reverse("transaction-cancel", args=[tx.id])
    response = auth_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_transaction_refund_success(auth_client, therapist_user):
    """Garante transição válida de PAID -> REFUNDED."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        paid_at=timezone.now(),
    )

    url = reverse("transaction-refund", args=[tx.id])
    response = auth_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["payment_status"] == "refunded"

    tx.refresh_from_db()
    assert tx.payment_status == FinancialTransaction.PaymentStatus.REFUNDED


@pytest.mark.django_db
def test_transaction_refund_invalid_state(auth_client, therapist_user):
    """Impede estornar uma transação pendente."""
    tx = FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date.today(),
    )

    url = reverse("transaction-refund", args=[tx.id])
    response = auth_client.post(url, {}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Testes de Isolamento Multi-Tenant ────────────────────────────────────────


@pytest.mark.django_db
def test_transaction_list_isolation(auth_client, auth_other_client, therapist_user, other_therapist):
    """Garante que a listagem de transações exibe apenas registros do terapeuta logado."""
    FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=100.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
    )
    FinancialTransaction.objects.create(
        therapist=other_therapist,
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        amount=200.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
    )

    url = reverse("transaction-list")

    # Terapeuta Principal
    res1 = auth_client.get(url)
    assert res1.status_code == status.HTTP_200_OK
    # Se paginado, checa resultados, senão checa lista direta
    results1 = res1.data.get("results", res1.data)
    assert len(results1) == 1
    assert results1[0]["amount"] == "100.00"

    # Outro Terapeuta
    res2 = auth_other_client.get(url)
    assert res2.status_code == status.HTTP_200_OK
    results2 = res2.data.get("results", res2.data)
    assert len(results2) == 1
    assert results2[0]["amount"] == "200.00"


@pytest.mark.django_db
def test_transaction_detail_isolation(auth_client, other_therapist):
    """Retorna 404 ao tentar ver detalhes de transação de outro terapeuta."""
    tx = FinancialTransaction.objects.create(
        therapist=other_therapist,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=100.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
    )

    url = reverse("transaction-detail", args=[tx.id])
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Teste de Exportação CSV ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_export_csv_success(auth_client, therapist_user):
    """Garante que a exportação gera um arquivo CSV com os dados filtrados e corretos."""
    FinancialTransaction.objects.create(
        therapist=therapist_user,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        category=FinancialTransaction.Category.SESSION,
        amount=150.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        description="=Sessão clínica",  # Possível injeção de fórmula
    )

    url = reverse("transaction-export-csv")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "text/csv; charset=utf-8-sig"

    # Analisa o conteúdo CSV retornado
    csv_file = io.StringIO(response.content.decode("utf-8-sig"))
    reader = csv.reader(csv_file, delimiter=";")
    rows = list(reader)

    # Cabeçalho + 1 linha
    assert len(rows) == 2
    assert rows[0][0] == "ID"
    # Valida o escape de CSV Injection na descrição
    assert rows[1][9] == "'=Sessão clínica"


# ── Teste de Consultas Não Faturadas ─────────────────────────────────────────


@pytest.mark.django_db
def test_unbilled_appointments_listing(
    auth_client, therapist_user, patient_of_therapist, other_therapist, patient_of_other_therapist
):
    """Lista apenas consultas confirmadas do próprio terapeuta que não possuem transações vinculadas."""
    now = timezone.now()

    # 1. Consulta confirmada e sem transação (deve ser listada)
    appt1 = Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=Appointment.Status.CONFIRMED,
        session_value=120.00,
    )

    # 2. Consulta confirmada e já faturada (não deve ser listada)
    appt2 = Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now - timedelta(days=1),
        end_time=now - timedelta(days=1, hours=-1),
        status=Appointment.Status.CONFIRMED,
        session_value=120.00,
    )
    FinancialTransaction.objects.create(
        therapist=therapist_user,
        appointment=appt2,
        amount=120.00,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
    )

    # 3. Consulta ainda agendada (scheduled) (não deve ser listada)
    Appointment.objects.create(
        therapist=therapist_user,
        patient=patient_of_therapist,
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5, hours=1),
        status=Appointment.Status.SCHEDULED,
        session_value=120.00,
    )

    # 4. Consulta confirmada de outro terapeuta (não deve ser listada)
    Appointment.objects.create(
        therapist=other_therapist,
        patient=patient_of_other_therapist,
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=Appointment.Status.CONFIRMED,
        session_value=150.00,
    )

    url = reverse("transaction-unbilled-appointments")
    response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["id"] == appt1.id
    assert response.data[0]["patient_name"] == "Paciente Principal"
