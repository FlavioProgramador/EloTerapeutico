from unittest.mock import patch

import pytest

from apps.organizations.api.v1.serializers import OrganizationSettingsSerializer
from apps.organizations.models import Organization, OrganizationMembership, OrganizationSettings
from apps.users.models import User


@pytest.mark.django_db
def test_organization_settings_serializer_memoizes_telemedicine_state():
    user = User.objects.create_user(
        email="owner@example.com",
        password="Password123!",
        full_name="Owner User",
    )
    organization = Organization.objects.create(
        name="Org Test",
        slug="org-test",
        created_by=user,
    )
    OrganizationMembership.objects.create(
        user=user,
        organization=organization,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )
    settings = OrganizationSettings.objects.get_or_create(organization=organization)[0]

    serializer = OrganizationSettingsSerializer(settings)

    # When serializing, _compute_telemedicine_state is executed exactly once
    with patch.object(
        serializer,
        "_compute_telemedicine_state",
        wraps=serializer._compute_telemedicine_state,
    ) as mock_compute:
        data = serializer.data
        assert mock_compute.call_count == 1
        assert "telemedicine_available" in data
        assert "telemedicine_unavailable_reason" in data
