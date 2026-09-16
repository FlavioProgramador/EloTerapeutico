from decimal import Decimal

from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.api.serializers import AppointmentRecurrenceSerializer
from apps.scheduling.models import Appointment, AppointmentRecurrence
from apps.users.models import User


class AppointmentRecurrencePerfTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recurrence_perf@example.com",
            password="password",
            full_name="Perf Therapist",
        )
        self.organization = Organization.objects.create(
            name="Perf Org",
            slug="perf-org-rec",
            created_by=self.user,
        )
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.ADMIN,
            status=OrganizationMembership.Status.ACTIVE,
        )
        self.patient = Patient.objects.create(
            organization=self.organization,
            full_name="Patient Perf",
            therapist=self.user,
        )

        for i in range(5):
            rec = AppointmentRecurrence.objects.create(
                organization=self.organization,
                patient=self.patient,
                therapist=self.user,
                frequency=AppointmentRecurrence.Frequency.WEEKLY,
                interval=1,
                starts_on=timezone.now().date(),
                start_time=timezone.now().time(),
                duration_minutes=50,
            )
            for j in range(5):
                Appointment.objects.create(
                    organization=self.organization,
                    patient=self.patient,
                    therapist=self.user,
                    recurrence=rec,
                    start_time=timezone.now() + timezone.timedelta(days=j),
                    end_time=timezone.now() + timezone.timedelta(days=j, minutes=50),
                    session_value=Decimal("150.00"),
                    status=Appointment.Status.COMPLETED if j % 2 == 0 else Appointment.Status.SCHEDULED,
                )

    def test_recurrence_list_queries_optimized(self):
        rf = RequestFactory()
        request = rf.get("/api/v1/scheduling/recurrences/")
        request.organization = self.organization
        request.organization_membership = self.membership
        request.user = self.user

        queryset = list(
            AppointmentRecurrence.objects.filter(organization=self.organization)
            .select_related("organization", "patient", "therapist", "room")
            .prefetch_related("appointments")
        )

        with CaptureQueriesContext(connection) as ctx:
            serializer = AppointmentRecurrenceSerializer(
                queryset, many=True, context={"request": request}
            )
            data = serializer.data

        self.assertEqual(len(ctx), 0)
        self.assertEqual(len(data), 5)
