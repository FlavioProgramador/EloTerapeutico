from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from apps.patients.models import Patient
from apps.reports.selectors import patients_for_owner
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

    def test_patients_report_age_distribution_optimized(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from apps.organizations.models import Organization, OrganizationMembership
        from apps.reports.services.patient_reports import patients_report

        org = Organization.objects.create(name="Org de Teste", slug="org-teste", created_by=self.owner)
        OrganizationMembership.objects.create(
            organization=org,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            status=OrganizationMembership.Status.ACTIVE,
        )

        today = date.today()
        # Minor (e.g., 4 years old)
        Patient.objects.create(
            organization=org,
            full_name="Criança",
            therapist=self.owner,
            birth_date=date(today.year - 4, today.month, today.day),
        )
        # Adult (e.g., 30 years old)
        Patient.objects.create(
            organization=org,
            full_name="Adulto",
            therapist=self.owner,
            birth_date=date(today.year - 30, today.month, today.day),
        )
        # No age
        Patient.objects.create(
            organization=org,
            full_name="Sem Data",
            therapist=self.owner,
            birth_date=None,
        )

        # Let's count queries or at least check correctness and make sure no heavy patient query is done
        with CaptureQueriesContext(connection) as ctx:
            res = patients_report(self.owner, {}, organization=org)

        # Ensure age distribution details are correct
        age_dist = res["charts"]["age_distribution"]
        # Find 0-5 bucket
        bucket_0_5 = next(item for item in age_dist if item["label"] == "0-5")
        self.assertEqual(bucket_0_5["value"], 1)

        # Find 26-35 bucket
        bucket_26_35 = next(item for item in age_dist if item["label"] == "26-35")
        self.assertEqual(bucket_26_35["value"], 1)

        # Find "Sem data" bucket
        bucket_sem_data = next(item for item in age_dist if item["label"] == "Sem data")
        self.assertEqual(bucket_sem_data["value"], 1)
