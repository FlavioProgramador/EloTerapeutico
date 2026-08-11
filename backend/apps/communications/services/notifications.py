from __future__ import annotations

from datetime import time
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import OrganizationMembership

from ..models import InAppNotification, NotificationDelivery, NotificationPreference

_ALLOWED_METADATA_KEYS = {
    "appointment_public_id",
    "patient_public_id",
    "document_public_id",
    "form_public_id",
    "billing_order_public_id",
    "source",
    "deduplication_key",
}


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if key not in _ALLOWED_METADATA_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = value
    return clean


def infer_notification_category(event_type: str) -> str:
    prefix = (event_type or "system").split(".", 1)[0]
    aliases = {
        "appointment": InAppNotification.Category.AGENDA,
        "agenda": InAppNotification.Category.AGENDA,
        "patient": InAppNotification.Category.PATIENTS,
        "patients": InAppNotification.Category.PATIENTS,
        "record": InAppNotification.Category.RECORDS,
        "records": InAppNotification.Category.RECORDS,
        "evolution": InAppNotification.Category.RECORDS,
        "document": InAppNotification.Category.DOCUMENTS,
        "documents": InAppNotification.Category.DOCUMENTS,
        "financial": InAppNotification.Category.FINANCIAL,
        "payment": InAppNotification.Category.FINANCIAL,
        "billing": InAppNotification.Category.BILLING,
        "subscription": InAppNotification.Category.BILLING,
        "communication": InAppNotification.Category.COMMUNICATIONS,
        "communications": InAppNotification.Category.COMMUNICATIONS,
        "form": InAppNotification.Category.FORMS,
        "forms": InAppNotification.Category.FORMS,
        "security": InAppNotification.Category.SECURITY,
        "auth": InAppNotification.Category.SECURITY,
    }
    return aliases.get(prefix, InAppNotification.Category.SYSTEM)


def get_notification_preferences(user) -> NotificationPreference:
    preference, _ = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={"timezone": getattr(user, "timezone", "America/Sao_Paulo")},
    )
    return preference


def category_channel_enabled(
    preference: NotificationPreference,
    category: str,
    channel: str,
) -> bool:
    category_config = (preference.category_preferences or {}).get(category, {})
    if isinstance(category_config, dict) and channel in category_config:
        return bool(category_config[channel])
    return bool(getattr(preference, f"{channel}_enabled", False))


def _inside_quiet_hours(
    preference: NotificationPreference,
    current: time | None = None,
) -> bool:
    if (
        not preference.quiet_hours_enabled
        or not preference.quiet_hours_start
        or not preference.quiet_hours_end
    ):
        return False
    current = current or timezone.localtime().time()
    start, end = preference.quiet_hours_start, preference.quiet_hours_end
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def _schedule_email_delivery(
    notification: InAppNotification,
    preference: NotificationPreference,
) -> None:
    if not category_channel_enabled(preference, notification.category, "email"):
        return
    delivery, created = NotificationDelivery.objects.get_or_create(
        notification=notification,
        channel=NotificationDelivery.Channel.EMAIL,
        defaults={
            "provider": "django_email",
            "status": NotificationDelivery.Status.PENDING,
            "scheduled_at": timezone.now(),
        },
    )
    if not created or _inside_quiet_hours(preference):
        return
    transaction.on_commit(lambda: _enqueue_notification_delivery(delivery.pk))


def _enqueue_notification_delivery(delivery_id: int) -> None:
    from ..tasks import send_notification_delivery

    send_notification_delivery.apply_async(args=[delivery_id], queue="communications")


def _resolve_notification_organization(*, organization, communication, recipient):
    if organization is not None:
        if communication is not None and communication.organization_id != organization.pk:
            raise ValidationError("A comunicação pertence a outra organização.")
        return organization
    if communication is not None and communication.organization_id:
        return communication.organization

    memberships = OrganizationMembership.objects.filter(
        user=recipient,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    membership = memberships.filter(is_default=True).first()
    if membership is None:
        first_two = list(memberships[:2])
        membership = first_two[0] if len(first_two) == 1 else None
    if membership is None:
        raise ValidationError("Não foi possível determinar a organização da notificação.")
    return membership.organization


@transaction.atomic
def create_notification(
    *,
    owner,
    recipient,
    title: str,
    message: str,
    event_type: str,
    category: str | None = None,
    priority: str = InAppNotification.Priority.NORMAL,
    internal_url: str = "",
    action_label: str = "",
    metadata: dict[str, Any] | None = None,
    actor=None,
    communication=None,
    organization=None,
    expires_at=None,
    deduplication_key: str = "",
) -> InAppNotification | None:
    organization = _resolve_notification_organization(
        organization=organization,
        communication=communication,
        recipient=recipient,
    )
    preference = get_notification_preferences(recipient)
    category = category or infer_notification_category(event_type)
    safe_metadata = _safe_metadata(metadata)
    if deduplication_key:
        safe_metadata["deduplication_key"] = deduplication_key[:160]
        existing = InAppNotification.objects.filter(
            organization=organization,
            recipient=recipient,
            notification_type=event_type,
            metadata__deduplication_key=deduplication_key[:160],
        ).first()
        if existing:
            return existing

    in_app_enabled = category_channel_enabled(preference, category, "in_app")
    email_enabled = category_channel_enabled(preference, category, "email")
    if not in_app_enabled and not email_enabled:
        return None

    notification = InAppNotification.objects.create(
        organization=organization,
        owner=owner,
        recipient=recipient,
        actor=actor,
        communication=communication,
        category=category,
        title=title[:160],
        message=message[:500],
        notification_type=event_type[:80],
        priority=priority,
        internal_url=internal_url[:500],
        action_label=action_label[:80],
        metadata=safe_metadata,
        expires_at=expires_at,
        archived_at=None if in_app_enabled else timezone.now(),
    )
    if in_app_enabled:
        NotificationDelivery.objects.create(
            notification=notification,
            channel=NotificationDelivery.Channel.IN_APP,
            status=NotificationDelivery.Status.DELIVERED,
            provider="elo_in_app",
            scheduled_at=notification.created_at or timezone.now(),
            sent_at=timezone.now(),
            delivered_at=timezone.now(),
        )
    _schedule_email_delivery(notification, preference)
    return notification


def notification_mark_read(notification: InAppNotification) -> InAppNotification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
    return notification


def notification_mark_unread(notification: InAppNotification) -> InAppNotification:
    if notification.is_read:
        notification.is_read = False
        notification.read_at = None
        notification.save(update_fields=["is_read", "read_at"])
    return notification


def notification_archive(notification: InAppNotification) -> InAppNotification:
    if notification.archived_at is None:
        notification.archived_at = timezone.now()
        notification.save(update_fields=["archived_at"])
    return notification
