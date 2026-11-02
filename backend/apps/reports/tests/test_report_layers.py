from datetime import date

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.reports.selectors import patients_for_owner
from apps.reports.services import patients_report
from apps.reports.services.periods import resolve_period
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
        self.patient = Patient.objects.create(full_name="Paciente do relatório", therapist=self.owner)
        Patient.objects.create(full_name="Paciente de outro tenant", therapist=self.other_owner)
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

    def test_patients_report_performance_and_metrics(self):
        org = Organization.objects.create(name="Org Relatórios", created_by=self.owner)
        OrganizationMembership.objects.create(
            organization=org,
            user=self.owner,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        today = timezone.localdate()
        p1 = Patient.objects.create(
            organization=org,
            therapist=self.owner,
            full_name="Paciente Um",
            birth_date=date(today.year - 20, today.month, today.day),
            is_active=True,
            status=Patient.Status.ACTIVE,
        )
        p2 = Patient.objects.create(
            organization=org,
            therapist=self.owner,
            full_name="Paciente Dois",
            birth_date=None,
            is_active=True,
            status=Patient.Status.ACTIVE,
        )

        with self.assertNumQueries(11):
            report = patients_report(self.owner, {}, organization=org)

        self.assertEqual(report["kpis"]["active_patients"], 2)
        self.assertEqual(report["kpis"]["evasion_risk"], 2)
        self.assertEqual(report["risk"]["count"], 2)

        age_dist = {item["label"]: item["value"] for item in report["charts"]["age_distribution"]}
        self.assertEqual(age_dist.get("18-25"), 1)
        self.assertEqual(age_dist.get("Sem data"), 1)
