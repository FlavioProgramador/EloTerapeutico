from django.contrib import admin

from apps.billing.models import WebhookEvent


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "gateway_name",
        "event_type",
        "event_id",
        "status",
        "attempt_count",
        "received_at",
        "processed_at",
    )
    list_filter = ("gateway_name", "event_type", "status", "received_at")
    search_fields = (
        "event_id",
        "payload_hash",
        "last_error",
        "error_message",
    )
    readonly_fields = (
        "gateway_name",
        "event_id",
        "event_type",
        "payload_hash",
        "payload",
        "attempt_count",
        "processed_at",
        "received_at",
        "updated_at",
    )
