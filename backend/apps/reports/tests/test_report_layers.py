from datetime import date
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.reports.selectors import patients_for_owner
from apps.reports.services.periods import resolve_period
from apps.scheduling.models import Appointment
from apps.users.models import User


class ReportLayerTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="report-owner@example.test",
            password="strong-password",
            full_name="Profissional Relatórios",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-report-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(
            full_name="Paciente do relatório",
            therapist=self.owner,
            birth_date=date(1990, 5, 15),
            payer_type=Patient.PayerType.INSURANCE,
            insurance_name="Convenio Top",
        )
        Patient.objects.create(
            full_name="Paciente de outro tenant",
            therapist=self.other_owner,
            birth_date=date(1985, 10, 20),
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            therapist=self.owner,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(minutes=50),
            session_value=Decimal("150.00"),
            status=Appointment.Status.COMPLETED,
        )
        self.transaction_income = FinancialTransaction.objects.create(
            patient=self.patient,
            therapist=self.owner,
            amount=Decimal("150.00"),
            paid_amount=Decimal("150.00"),
            transaction_type=FinancialTransaction.TransactionType.INCOME,
            payment_status=FinancialTransaction.PaymentStatus.PAID,
            due_date=timezone.now().date(),
        )
        self.transaction_overdue = FinancialTransaction.objects.create(
            patient=self.patient,
            therapist=self.owner,
            amount=Decimal("200.00"),
            paid_amount=Decimal("0.00"),
            transaction_type=FinancialTransaction.TransactionType.INCOME,
            payment_status=FinancialTransaction.PaymentStatus.PENDING,
            due_date=timezone.now().date() - timezone.timedelta(days=10),
        )
        self.client.force_authenticate(self.owner)

    def test_patient_selector_does_not_leak_other_owner(self):
        self.assertQuerySetEqual(patients_for_owner(owner=self.owner), [self.patient])

    def test_custom_period_is_resolved_without_changing_contract(self):
        start, end = resolve_period({"start_date": "2026-01-01", "end_date": "2026-01-31"})
        self.assertEqual(start, date(2026, 1, 1))
        self.assertEqual(end, date(2026, 1, 31))

    def test_invalid_period_keeps_existing_api_error(self):
        response = self.client.get(
            "/api/v1/reports/patients/",
            {"start_date": "2026-02-01", "end_date": "2026-01-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"detail": "Periodo invalido. Confira a data inicial e a data final informadas."},
        )

    def test_invalid_export_type_keeps_existing_api_error(self):
        response = self.client.get("/api/v1/reports/export/", {"type": "unknown"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Tipo de relatorio invalido."})

    def test_reports_optimized_footprint(self):
        # Test patients report
        response = self.client.get("/api/v1/reports/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("kpis", response.data)
        self.assertIn("charts", response.data)
        self.assertIn("risk", response.data)
        self.assertIn("age_distribution", response.data["charts"])

        # Test appointments report
        response = self.client.get("/api/v1/reports/appointments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("kpis", response.data)
        self.assertIn("charts", response.data)
        self.assertIn("table", response.data)
        self.assertIn("by_insurance", response.data["charts"])

        # Test financial report
        response = self.client.get("/api/v1/reports/financial/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("kpis", response.data)
        self.assertIn("delinquency_by_patient", response.data)
        self.assertIn("revenue_by_insurance", response.data)
        self.assertIn("dre", response.data)
        self.assertIn("projection", response.data)
        self.assertIn("transactions", response.data)
