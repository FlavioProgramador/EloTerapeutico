from __future__ import annotations

import pytest
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.communications.models import (
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationTemplate,
)
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


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
    user.test_organization = organization
    return organization


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email="automations.perf.therapist@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Automação Perf",
        role=User.Role.THERAPIST,
        phone="21999998888",
        onboarding_completed_at=timezone.now(),
    )
    _create_tenant(user, "automations-perf-therapist")
    return user


@pytest.fixture
def authenticated_client(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(therapist.test_organization.pk)
    )
    return client


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_automations_list_queries_optimized(authenticated_client, therapist):
    organization = therapist.test_organization
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=therapist,
        name="Template Teste",
        slug="template-teste",
        channel="email",
        category="appointment_reminder",
        subject_template="Lembrete",
        body_template="Olá {{patient_name}}",
        created_by=therapist,
        updated_by=therapist,
    )

    num_automations = 10
    now = timezone.now()

    for i in range(num_automations):
        automation = CommunicationAutomation.objects.create(
            organization=organization,
            owner=therapist,
            name=f"Automação {i:02d}",
            event_type="appointment_created",
            channel="email",
            template=template,
            created_by=therapist,
            updated_by=therapist,
        )

        # Create 3 runs for each automation: 1 successful, 2 failed
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_created",
            status=CommunicationAutomationRun.Status.FAILED,
            idempotency_key=f"run:{i}:1",
            started_at=now - timezone.timedelta(minutes=30),
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_created",
            status=CommunicationAutomationRun.Status.CREATED,
            idempotency_key=f"run:{i}:2",
            started_at=now - timezone.timedelta(minutes=15),
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment_created",
            status=CommunicationAutomationRun.Status.FAILED,
            idempotency_key=f"run:{i}:3",
            started_at=now - timezone.timedelta(minutes=5),
        )

    # Warm up call (handles session / auth / content type lazy loading)
    authenticated_client.get("/api/v1/communications/automations/")

    with CaptureQueriesContext(connection) as queries_context:
        response = authenticated_client.get("/api/v1/communications/automations/")

    assert response.status_code == 200
    results = response.data["results"]
    assert len(results) == num_automations

    # Verify each item's serialized values
    for item in results:
        assert item["failures"] == 2
        assert item["last_run_at"] is not None

    total_queries = len(queries_context)
    # With optimization, query count is small and constant regardless of N automations.
    assert total_queries <= 10, f"Expected <= 10 queries, got {total_queries}"
