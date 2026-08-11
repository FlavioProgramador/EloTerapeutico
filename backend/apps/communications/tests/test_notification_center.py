from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.communications.models import InAppNotification, NotificationPreference
from apps.communications.services.notifications import create_notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

pytestmark = pytest.mark.django_db


def user(email: str) -> User:
    current_user = User.objects.create_user(
        email=email,
        password="SenhaForte123!",
        full_name="Usuário Notificações",
    )
    slug = email.split("@", 1)[0].replace(".", "-")
    organization = Organization.objects.create(
        name=f"Organização de {current_user.full_name}",
        slug=slug,
        organization_type=Organization.Type.INDIVIDUAL,
        status=Organization.Status.ACTIVE,
        created_by=current_user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=current_user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    current_user.test_organization = organization
    return current_user


def authenticated_client(current_user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(current_user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(current_user.test_organization.pk)
    )
    return client


def create_item(owner: User, **kwargs) -> InAppNotification:
    return InAppNotification.objects.create(
        organization=owner.test_organization,
        owner=owner,
        recipient=owner,
        category=kwargs.pop("category", InAppNotification.Category.SYSTEM),
        title=kwargs.pop("title", "Aviso"),
        message=kwargs.pop("message", "Mensagem administrativa"),
        notification_type=kwargs.pop("notification_type", "system.notice"),
        **kwargs,
    )


def test_notification_api_isolates_recipient_and_uses_public_id():
    owner = user("notification-owner@example.test")
    other = user("notification-other@example.test")
    own_notification = create_item(owner)
    other_notification = create_item(other, title="Outro usuário")
    client = authenticated_client(owner)

    listing = client.get("/api/v1/communications/notifications/")
    detail = client.get(
        f"/api/v1/communications/notifications/{own_notification.public_id}/"
    )
    forbidden_detail = client.get(
        f"/api/v1/communications/notifications/{other_notification.public_id}/"
    )

    assert listing.status_code == 200
    assert [item["public_id"] for item in listing.data["results"]] == [
        str(own_notification.public_id)
    ]
    assert detail.status_code == 200
    assert forbidden_detail.status_code == 404
    assert "id" not in detail.data


def test_read_unread_archive_and_bulk_actions():
    owner = user("notification-actions@example.test")
    first = create_item(owner)
    second = create_item(owner, title="Segundo")
    client = authenticated_client(owner)

    assert client.post(
        f"/api/v1/communications/notifications/{first.public_id}/read/"
    ).status_code == 200
    assert client.post(
        f"/api/v1/communications/notifications/{first.public_id}/unread/"
    ).status_code == 200
    assert client.post(
        "/api/v1/communications/notifications/read-all/"
    ).data["updated"] == 2
    assert client.post(
        "/api/v1/communications/notifications/archive-read/"
    ).data["updated"] == 2

    first.refresh_from_db()
    second.refresh_from_db()
    assert first.archived_at is not None
    assert second.archived_at is not None


def test_preferences_are_private_and_whatsapp_cannot_be_enabled():
    owner = user("notification-preferences@example.test")
    other = user("notification-preferences-other@example.test")
    NotificationPreference.objects.create(user=other, email_enabled=False)
    client = authenticated_client(owner)

    response = client.patch(
        "/api/v1/communications/notifications/preferences/",
        {
            "email_enabled": False,
            "category_preferences": {"agenda": {"in_app": True, "email": False}},
        },
        format="json",
    )
    invalid = client.patch(
        "/api/v1/communications/notifications/preferences/",
        {"whatsapp_enabled": True},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["email_enabled"] is False
    assert invalid.status_code == 400
    assert NotificationPreference.objects.get(user=other).email_enabled is False


def test_service_deduplicates_and_sanitizes_metadata():
    owner = user("notification-service@example.test")
    organization = owner.test_organization
    NotificationPreference.objects.create(user=owner, email_enabled=False)

    first = create_notification(
        organization=organization,
        owner=owner,
        recipient=owner,
        title="Consulta alterada",
        message="Uma consulta foi atualizada.",
        event_type="appointment.updated",
        metadata={"source": "agenda", "cpf": "não armazenar"},
        deduplication_key="appointment:123:updated",
    )
    second = create_notification(
        organization=organization,
        owner=owner,
        recipient=owner,
        title="Consulta alterada novamente",
        message="Duplicada",
        event_type="appointment.updated",
        deduplication_key="appointment:123:updated",
    )

    assert first is not None
    assert second is not None
    assert first.pk == second.pk
    assert first.category == InAppNotification.Category.AGENDA
    assert "cpf" not in first.metadata
