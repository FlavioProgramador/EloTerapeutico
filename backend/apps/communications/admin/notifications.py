from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.communications.models import (
    InAppNotification,
    InboundMessage,
    NotificationDelivery,
    NotificationPreference,
)

from .base import ReadOnlyHistoryAdmin


@admin.register(InAppNotification)
class InAppNotificationAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "recipient",
        "title",
        "notification_type",
        "priority",
        "is_read",
        "created_at",
    )
    list_filter = ("notification_type", "priority", "is_read", "created_at")
    search_fields = ("title", "recipient__email")
    readonly_fields = tuple(field.name for field in InAppNotification._meta.fields)
    list_select_related = ("owner", "recipient", "communication")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(ModelAdmin):
    list_display = (
        "user",
        "in_app_enabled",
        "email_enabled",
        "whatsapp_enabled",
        "quiet_hours_enabled",
        "updated_at",
    )
    list_filter = (
        "in_app_enabled",
        "email_enabled",
        "whatsapp_enabled",
        "quiet_hours_enabled",
    )
    search_fields = ("user__email", "user__full_name")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "notification",
        "channel",
        "status",
        "attempt_count",
        "scheduled_at",
        "sent_at",
    )
    list_filter = ("channel", "status")
    search_fields = (
        "notification__title",
        "notification__recipient__email",
        "provider_reference",
    )
    readonly_fields = tuple(field.name for field in NotificationDelivery._meta.fields)


@admin.register(InboundMessage)
class InboundMessageAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "owner",
        "sender_masked",
        "channel",
        "provider",
        "status",
        "received_at",
    )
    list_filter = ("channel", "provider", "status", "received_at")
    search_fields = ("sender_masked", "external_id", "owner__email")
    readonly_fields = tuple(field.name for field in InboundMessage._meta.fields)
    list_select_related = (
        "owner",
        "patient",
        "communication",
        "reviewed_by",
    )
