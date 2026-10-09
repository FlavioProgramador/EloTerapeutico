from __future__ import annotations

from datetime import timedelta
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User
from apps.communications.models import (
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationTemplate,
)
from apps.communications.api.v1.serializers.automations import (
    CommunicationAutomationSerializer,
)


def _create_tenant(user: User, slug: str) -> Organization:
    organization = Organization.objects.create(
        name=f"Organização de {user.full_name}",
        slug=slug,
        organization_type=Organization.Type.INDIVIDUAL,
        status=Organization.Status.ACTIVE,
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    return organization


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email="automations.therapist@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Automações",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    user.test_organization = _create_tenant(user, "automations-therapist")
    return user


@pytest.mark.django_db
def test_communication_automation_serializer_prefetched_runs_query_count(therapist):
    organization = therapist.test_organization
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=therapist,
        name="Template Exemplo",
        channel="email",
        created_by=therapist,
        updated_by=therapist,
    )

    now = timezone.now()
    # Create 5 automations, each with 3 runs (one failed, two started)
    for i in range(5):
        automation = CommunicationAutomation.objects.create(
            organization=organization,
            owner=therapist,
            name=f"Automação {i}",
            event_type="appointment_scheduled",
            channel="email",
            template=template,
            created_by=therapist,
            updated_by=therapist,
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_scheduled",
            status=CommunicationAutomationRun.Status.STARTED,
            started_at=now - timedelta(minutes=10 * (i + 1)),
            idempotency_key=f"run1:{i}",
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_scheduled",
            status=CommunicationAutomationRun.Status.FAILED,
            started_at=now - timedelta(minutes=5 * (i + 1)),
            idempotency_key=f"run2:{i}",
        )

    # Queryset with prefetch_related("runs")
    qs = (
        CommunicationAutomation.objects.filter(organization=organization)
        .select_related("organization", "template", "owner")
        .prefetch_related("runs")
    )

    # Evaluate queryset to load cache
    automations = list(qs)

    # Serializing all prefetched automations should perform 0 additional SQL queries
    with CaptureQueriesContext(connection) as queries:
        serializer = CommunicationAutomationSerializer(
            automations,
            many=True,
            context={"request": None},
        )
        data = serializer.data

    assert len(queries) == 0
    assert len(data) == 5
    for item in data:
        assert item["failures"] == 1
        assert item["last_run_at"] is not None


@pytest.mark.django_db
def test_communication_automation_viewset_list_queries_optimized(therapist):
    organization = therapist.test_organization
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=therapist,
        name="Template Exemplo Viewset",
        channel="email",
        created_by=therapist,
        updated_by=therapist,
    )

    now = timezone.now()
    for i in range(5):
        automation = CommunicationAutomation.objects.create(
            organization=organization,
            owner=therapist,
            name=f"Automação Viewset {i}",
            event_type="appointment_scheduled",
            channel="email",
            template=template,
            created_by=therapist,
            updated_by=therapist,
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_scheduled",
            status=CommunicationAutomationRun.Status.FAILED,
            started_at=now - timedelta(minutes=i + 1),
            idempotency_key=f"viewset_run:{i}",
        )

    client = APIClient()
    client.force_authenticate(therapist)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))

    # Warm up auth and session
    client.get("/api/v1/communications/automations/")

    with CaptureQueriesContext(connection) as queries:
        response = client.get("/api/v1/communications/automations/")

    assert response.status_code == 200
    # Queries should be constant (no N+1 per automation)
    assert len(queries) <= 6
