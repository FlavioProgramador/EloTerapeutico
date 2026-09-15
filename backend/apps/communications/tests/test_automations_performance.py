import pytest
from datetime import timedelta
from django.utils import timezone

from apps.communications.api.v1.serializers import CommunicationAutomationSerializer
from apps.communications.models import (
    Communication,
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationTemplate,
)
from apps.organizations.models import Organization
from apps.users.models import User


@pytest.mark.django_db
def test_communication_automation_serializer_prefetched_runs_query_count(django_assert_num_queries):
    user = User.objects.create_user(
        email="user_test@example.com",
        password="password123",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Org Teste", slug="org-teste", created_by=user
    )
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=user,
        name="Template Teste",
        slug="template-teste",
        category=Communication.Category.APPOINTMENT_REMINDER,
        channel=Communication.Channel.EMAIL,
        body_template="Olá {{ paciente_nome }}",
    )

    now = timezone.now()
    automations = []
    for i in range(5):
        auto = CommunicationAutomation.objects.create(
            organization=organization,
            owner=user,
            name=f"Automação {i}",
            event_type="appointment_created",
            channel=Communication.Channel.EMAIL,
            template=template,
        )
        # Create successful run
        CommunicationAutomationRun.objects.create(
            automation=auto,
            source_event="appointment_created",
            status=CommunicationAutomationRun.Status.CREATED,
            idempotency_key=f"run_success_{i}",
            started_at=now - timedelta(minutes=10),
        )
        # Create failed run (latest)
        CommunicationAutomationRun.objects.create(
            automation=auto,
            source_event="appointment_created",
            status=CommunicationAutomationRun.Status.FAILED,
            idempotency_key=f"run_fail_{i}",
            started_at=now - timedelta(minutes=5),
        )
        automations.append(auto)

    # Fetch with prefetch_related("runs")
    queryset = (
        CommunicationAutomation.objects.filter(organization=organization)
        .select_related("template")
        .prefetch_related("runs")
    )
    items = list(queryset)  # Force evaluation

    # Serializing prefetched objects should execute 0 additional queries
    with django_assert_num_queries(0):
        data = CommunicationAutomationSerializer(
            items, many=True, context={"request": None}
        ).data

    assert len(data) == 5
    for item in data:
        assert item["failures"] == 1
        assert item["last_run_at"] is not None


@pytest.mark.django_db
def test_communication_automation_serializer_unprefetched_fallback():
    user = User.objects.create_user(
        email="user_unpref@example.com",
        password="password123",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Org Teste Unprefetched", slug="org-teste-unpref", created_by=user
    )
    template = CommunicationTemplate.objects.create(
        organization=organization,
        owner=user,
        name="Template Teste",
        slug="template-teste-unpref",
        category=Communication.Category.APPOINTMENT_REMINDER,
        channel=Communication.Channel.EMAIL,
        body_template="Olá",
    )

    auto = CommunicationAutomation.objects.create(
        organization=organization,
        owner=user,
        name="Automação Sem Prefetch",
        event_type="appointment_created",
        channel=Communication.Channel.EMAIL,
        template=template,
    )

    # Serializing single instance without prefetch
    data = CommunicationAutomationSerializer(auto, context={"request": None}).data
    assert data["failures"] == 0
    assert data["last_run_at"] is None
