import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.communications.models import (
    Communication,
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationTemplate,
)
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User


@pytest.fixture
def org_and_user(db):
    user = User.objects.create_user(
        email="automation_tester@example.com",
        password="safe-password-123",
        full_name="Testador Automações",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Clínica de Testes",
        slug="clinica-testes",
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    return organization, user


@pytest.fixture
def client(org_and_user):
    organization, user = org_and_user
    api_client = APIClient()
    api_client.force_authenticate(user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return api_client


def create_automations_with_runs(organization, user, count):
    now = timezone.now()
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=user,
        name=f"Template de Lembrete {now.timestamp()}",
        slug=f"lembrete-{now.timestamp()}",
        channel=Communication.Channel.EMAIL,
        category=Communication.Category.APPOINTMENT_REMINDER,
        body_template="Olá, seu agendamento é amanhã.",
        is_active=True,
    )
    for i in range(count):
        automation = CommunicationAutomation.objects.create(
            organization=organization,
            owner=user,
            created_by=user,
            updated_by=user,
            name=f"Automação {i}-{now.timestamp()}",
            event_type="appointment.scheduled",
            channel=Communication.Channel.EMAIL,
            template=template,
            is_active=True,
        )
        # Create a successful run and a failed run
        CommunicationAutomationRun.objects.create(
            automation=automation,
            status=CommunicationAutomationRun.Status.CREATED,
            started_at=now,
            idempotency_key=f"run1-{automation.pk}",
        )
        CommunicationAutomationRun.objects.create(
            automation=automation,
            status=CommunicationAutomationRun.Status.FAILED,
            started_at=now + timezone.timedelta(minutes=5),
            idempotency_key=f"run2-{automation.pk}",
        )


@pytest.mark.django_db
def test_automation_list_queries_are_constant(client, org_and_user):
    organization, user = org_and_user

    # Warmup request
    client.get("/api/v1/communications/automations/")

    # Create 2 automations with runs
    create_automations_with_runs(organization, user, 2)

    with CaptureQueriesContext(connection) as queries_small:
        response_small = client.get("/api/v1/communications/automations/")
        assert response_small.status_code == 200
        count_small = len(queries_small)

    # Create 3 more automations (total 5)
    create_automations_with_runs(organization, user, 3)

    with CaptureQueriesContext(connection) as queries_large:
        response_large = client.get("/api/v1/communications/automations/")
        assert response_large.status_code == 200
        count_large = len(queries_large)

    # Query count should remain constant regardless of the number of automations
    assert count_large == count_small

    # Verify serialization details
    results = response_large.data["results"] if isinstance(response_large.data, dict) and "results" in response_large.data else response_large.data
    assert len(results) == 5
    for item in results:
        assert item["failures"] == 1
        assert item["last_run_at"] is not None
