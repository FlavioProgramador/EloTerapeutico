from __future__ import annotations

import uuid

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.communications.api.v1.serializers.automations import (
    CommunicationAutomationSerializer,
)
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
    return organization


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_communication_automation_serializer_uses_prefetched_runs(django_assert_num_queries):
    uid = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f"perf_auto_{uid}@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Perf",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    org = _create_tenant(user, f"slug-auto-{uid}")
    template = CommunicationTemplate.objects.create(
        organization=org,
        owner=user,
        name="Template Teste",
        channel="email",
        created_by=user,
        updated_by=user,
    )

    now = timezone.now()
    automations = []
    for i in range(3):
        auto = CommunicationAutomation.objects.create(
            organization=org,
            name=f"Automação {i}",
            channel="email",
            template=template,
            owner=user,
            created_by=user,
            updated_by=user,
        )
        automations.append(auto)
        # Add 3 runs: 1 failed, 2 started
        for j in range(3):
            CommunicationAutomationRun.objects.create(
                automation=auto,
                source_event="appointment.created",
                source_object_type="appointment",
                source_object_id=str(j),
                idempotency_key=f"run-{i}-{j}",
                status=(
                    CommunicationAutomationRun.Status.FAILED
                    if j == 0
                    else CommunicationAutomationRun.Status.STARTED
                ),
                started_at=now + timezone.timedelta(minutes=j * 10),
            )

    # Pre-load queryset with prefetch_related
    qs = list(
        CommunicationAutomation.objects.filter(organization=org)
        .select_related("organization", "template", "owner")
        .prefetch_related("runs")
    )

    # Verify that serialization executes ZERO additional SQL queries
    with django_assert_num_queries(0):
        data = CommunicationAutomationSerializer(qs, many=True).data

    assert len(data) == 3
    for item in data:
        assert item["failures"] == 1
        assert item["last_run_at"] is not None


@pytest.mark.django_db
@override_settings(BILLING_REQUIRE_SUBSCRIPTION=False)
def test_communication_automation_serializer_fallback_without_prefetch():
    uid = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f"fallback_auto_{uid}@example.test",
        password="SenhaForte123!",
        full_name="Terapeuta Fallback",
        role=User.Role.THERAPIST,
        onboarding_completed_at=timezone.now(),
    )
    org = _create_tenant(user, f"slug-fallback-{uid}")
    template = CommunicationTemplate.objects.create(
        organization=org,
        owner=user,
        name="Template Fallback",
        channel="email",
        created_by=user,
        updated_by=user,
    )

    now = timezone.now()
    auto = CommunicationAutomation.objects.create(
        organization=org,
        name="Automação Fallback",
        channel="email",
        template=template,
        owner=user,
        created_by=user,
        updated_by=user,
    )
    run1 = CommunicationAutomationRun.objects.create(
        automation=auto,
        source_event="event",
        source_object_type="obj",
        source_object_id="1",
        idempotency_key="key-1",
        status=CommunicationAutomationRun.Status.FAILED,
        started_at=now,
    )
    run2 = CommunicationAutomationRun.objects.create(
        automation=auto,
        source_event="event",
        source_object_type="obj",
        source_object_id="2",
        idempotency_key="key-2",
        status=CommunicationAutomationRun.Status.STARTED,
        started_at=now + timezone.timedelta(hours=1),
    )

    # Fetch without prefetch_related
    auto_from_db = CommunicationAutomation.objects.get(pk=auto.pk)
    data = CommunicationAutomationSerializer(auto_from_db).data

    assert data["failures"] == 1
    assert data["last_run_at"] == run2.started_at
