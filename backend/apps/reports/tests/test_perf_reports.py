from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.finances.models import FinancialTransaction
from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.reports.services import appointments_report, financial_report, patients_report
from apps.scheduling.models import Appointment
from apps.users.models import User


@pytest.fixture
def setup_data(db):
    therapist = User.objects.create_user(
        email="therapist_reports_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Reports Perf",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Clinica Perf Test",
        created_by=therapist,
    )
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=therapist,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )

    # Create some patients
    patient1 = Patient.objects.create(
        organization=organization,
        therapist=therapist,
        full_name="Ana Silva",
        social_name="Aninha",
        birth_date=date(1990, 5, 15),
        payer_type=Patient.PayerType.PRIVATE,
        status=Patient.Status.ACTIVE,
    )
    patient2 = Patient.objects.create(
        organization=organization,
        therapist=therapist,
        full_name="Carlos Souza",
        birth_date=date(2015, 8, 20),  # Under 18, has guardian
        guardian_name="Maria Souza",
        payer_type=Patient.PayerType.INSURANCE,
        insurance_name="Unimed",
        status=Patient.Status.ACTIVE,
    )
    patient3 = Patient.objects.create(
        organization=organization,
        therapist=therapist,
        full_name="Sem Data Nasc",
        payer_type=Patient.PayerType.PRIVATE,
        status=Patient.Status.INACTIVE,
    )

    # Create appointments
    now = timezone.now()
    appt1 = Appointment.objects.create(
        organization=organization,
        patient=patient1,
        therapist=therapist,
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=2) + timedelta(hours=1),
        status=Appointment.Status.COMPLETED,
        session_value=Decimal("150.00"),
    )
    appt2 = Appointment.objects.create(
        organization=organization,
        patient=patient2,
        therapist=therapist,
        start_time=now - timedelta(days=1),
        end_time=now - timedelta(days=1) + timedelta(hours=1),
        status=Appointment.Status.COMPLETED,
        session_value=Decimal("120.00"),
    )
    # Future appointment
    appt3 = Appointment.objects.create(
        organization=organization,
        patient=patient1,
        therapist=therapist,
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5) + timedelta(hours=1),
        status=Appointment.Status.CONFIRMED,
        session_value=Decimal("150.00"),
    )

    # Create transactions
    FinancialTransaction.objects.create(
        organization=organization,
        therapist=therapist,
        patient=patient1,
        appointment=appt1,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        category="session",
        amount=Decimal("150.00"),
        paid_amount=Decimal("150.00"),
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        due_date=now.date() - timedelta(days=2),
    )
    # Overdue transaction
    FinancialTransaction.objects.create(
        organization=organization,
        therapist=therapist,
        patient=patient2,
        appointment=appt2,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        category="session",
        amount=Decimal("120.00"),
        paid_amount=Decimal("0.00"),
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=now.date() - timedelta(days=5),
    )

    return therapist, organization, membership


@pytest.mark.django_db
def test_reports_performance_and_correctness(setup_data):
    therapist, organization, membership = setup_data

    # Test patients report
    params = {"start_date": "2026-01-01", "end_date": "2026-12-31"}
    data_patients = patients_report(therapist, params, organization=organization)

    assert "kpis" in data_patients
    assert data_patients["kpis"]["active_patients"] == 2
    assert "charts" in data_patients
    age_dist = {item["label"]: item["value"] for item in data_patients["charts"]["age_distribution"]}
    assert age_dist["Sem data"] == 1

    # Test appointments report
    data_appts = appointments_report(therapist, params, organization=organization)
    assert "kpis" in data_appts
    assert data_appts["kpis"]["total"] == 3

    by_ins = {item["label"]: item["value"] for item in data_appts["charts"]["by_insurance"]}
    assert by_ins["Particular"] == 2
    assert by_ins["Unimed"] == 1

    # Test financial report
    data_fin = financial_report(therapist, params, organization=organization)
    assert "kpis" in data_fin
    assert data_fin["kpis"]["overdue_titles"] == 1
    assert data_fin["kpis"]["overdue_value"] == 120.0

    rev_ins = {item["label"]: item["value"] for item in data_fin["revenue_by_insurance"]}
    assert rev_ins["Particular"] == 150.0
