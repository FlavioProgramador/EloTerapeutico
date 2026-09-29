from __future__ import annotations

import pytest

from apps.organizations.api.v1.serializers import OrganizationSettingsSerializer
from apps.organizations.models import Organization, OrganizationMembership, OrganizationSettings
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_organization_settings_serializer_memoizes_telemedicine_queries(django_assert_num_queries, monkeypatch):
    monkeypatch.setenv("TELEMEDICINE_ENABLED", "true")
    monkeypatch.setenv("TELEMEDICINE_PROVIDER", "fake")

    owner = User.objects.create_user(
        email="owner-settings@example.test",
        full_name="Owner Settings",
        password="TestPassword2026!",
        role=User.Role.THERAPIST,
    )
    organization = Organization.objects.create(
        name="Org Settings Test",
        slug="org-settings-test",
        organization_type=Organization.Type.INDIVIDUAL,
        created_by=owner,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=owner,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    settings = OrganizationSettings.objects.create(
        organization=organization,
        allow_telemedicine=True,
    )

    serializer = OrganizationSettingsSerializer(settings)

    # 1 query for OrganizationMembership (owner) + 1 query for Subscription (latest subscription) = 2 queries total.
    # Without memoization, get_telemedicine_available and get_telemedicine_unavailable_reason each run 2 queries = 4 queries.
    with django_assert_num_queries(2):
        data = serializer.data

    assert "telemedicine_available" in data
    assert "telemedicine_unavailable_reason" in data
