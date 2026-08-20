from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.communications.models import (
    Communication,
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
    return organization


@pytest.fixture
def therapist(db):
    user = User.objects.create_user(
        email="automations.perf@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Automações Perf",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    user.test_organization = _create_tenant(user, "automations-perf")
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
def test_automation_list_queries_are_constant(
    authenticated_client,
    therapist,
    django_assert_num_queries,
):
    organization = therapist.test_organization
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=therapist,
        name="Template de Teste",
        slug="template-de-teste",
        category=Communication.Category.PATIENT_MESSAGE,
        channel=Communication.Channel.EMAIL,
        subject_template="Assunto",
        body_template="Corpo",
        created_by=therapist,
    )

    now = timezone.now()
    num_automations = 5

    for i in range(num_automations):
        automation = CommunicationAutomation.objects.create(
            organization=organization,
            owner=therapist,
            name=f"Automação {i}",
            event_type="appointment.created",
            channel=Communication.Channel.EMAIL,
            template=template,
            created_by=therapist,
        )
        # Create successful and failed runs
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment.created",
            status=CommunicationAutomationRun.Status.CREATED,
            idempotency_key=f"run:{i}:1",
            started_at=now - timedelta(minutes=10),
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            source_event="appointment.created",
            status=CommunicationAutomationRun.Status.FAILED,
            idempotency_key=f"run:{i}:2",
            started_at=now - timedelta(minutes=5),
        )

    # Queries expected:
    # 1. Subscription check for active user
    # 2. OrganizationMembership lookup for tenant context / permission
    # 3. DRF pagination COUNT query
    # 4. CommunicationAutomation list query (select_related organization, template, owner)
    # 5. Prefetch CommunicationAutomationRun for all returned automations
    with django_assert_num_queries(5):
        response = authenticated_client.get("/api/v1/communications/automations/")

    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) == num_automations
    for item in results:
        assert item["failures"] == 1
        assert item["last_run_at"] is not None
