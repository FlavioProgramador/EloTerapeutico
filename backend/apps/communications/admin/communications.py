from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.communications.models import (
    Communication,
    CommunicationAttempt,
    CommunicationPreference,
    CommunicationRecipient,
    CommunicationTemplate,
    PublicCommunicationActionToken,
)

from .base import ReadOnlyHistoryAdmin


@admin.register(Communication)
class CommunicationAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "owner",
        "patient",
        "channel",
        "category",
        "status_badge",
        "scheduled_at",
        "created_at",
    )
    list_filter = ("channel", "category", "status", "priority", "created_at")
    search_fields = (
        "id",
        "public_id",
        "subject",
        "owner__email",
        "patient__full_name",
        "source_event",
    )
    readonly_fields = tuple(field.name for field in Communication._meta.fields)
    list_select_related = ("owner", "patient", "appointment", "created_by")
    date_hierarchy = "created_at"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            Communication.Status.DELIVERED: "#15803d",
            Communication.Status.SENT: "#0369a1",
            Communication.Status.FAILED: "#b91c1c",
            Communication.Status.SCHEDULED: "#a16207",
            Communication.Status.QUEUED: "#6d28d9",
        }
        return format_html(
            '<span style="background:{};color:white;padding:3px 8px;border-radius:999px">{}</span>',
            colors.get(obj.status, "#475569"),
            obj.get_status_display(),
        )


@admin.register(CommunicationRecipient)
class CommunicationRecipientAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "communication",
        "recipient_type",
        "name",
        "destination_masked",
        "channel",
        "status",
    )
    list_filter = ("recipient_type", "channel", "status")
    search_fields = ("communication__id", "name", "destination_masked")
    readonly_fields = tuple(
        field.name for field in CommunicationRecipient._meta.fields
    )
    list_select_related = ("communication", "patient")


@admin.register(CommunicationAttempt)
class CommunicationAttemptAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "communication",
        "attempt_number",
        "provider",
        "status",
        "started_at",
        "finished_at",
    )
    list_filter = ("provider", "status", "created_at")
    search_fields = ("communication__id", "external_id", "error_code")
    readonly_fields = tuple(
        field.name for field in CommunicationAttempt._meta.fields
    )
    list_select_related = ("communication", "recipient")


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(ModelAdmin):
    list_display = (
        "name",
        "owner",
        "channel",
        "category",
        "is_system_template",
        "is_active",
        "is_archived",
    )
    list_filter = (
        "channel",
        "category",
        "is_system_template",
        "is_active",
        "is_archived",
    )
    search_fields = ("name", "slug", "description", "owner__email")
    readonly_fields = (
        "allowed_variables",
        "is_system_template",
        "created_at",
        "updated_at",
    )
    list_select_related = ("owner", "created_by", "updated_by")


@admin.register(CommunicationPreference)
class CommunicationPreferenceAdmin(ModelAdmin):
    list_display = (
        "patient",
        "owner",
        "preferred_channel",
        "general_opt_out",
        "allow_email",
        "allow_whatsapp",
        "updated_at",
    )
    list_filter = (
        "preferred_channel",
        "general_opt_out",
        "allow_email",
        "allow_whatsapp",
        "allow_sms",
    )
    search_fields = ("patient__full_name", "owner__email")
    list_select_related = ("owner", "patient", "consent_recorded_by")


@admin.register(PublicCommunicationActionToken)
class PublicCommunicationActionTokenAdmin(ReadOnlyHistoryAdmin):
    list_display = (
        "id",
        "owner",
        "purpose",
        "patient",
        "appointment",
        "expires_at",
        "used_at",
        "revoked_at",
    )
    list_filter = ("purpose", "expires_at", "used_at", "revoked_at")
    search_fields = ("owner__email", "patient__full_name", "appointment__id")
    exclude = ("token_hash",)
    readonly_fields = tuple(
        field.name
        for field in PublicCommunicationActionToken._meta.fields
        if field.name != "token_hash"
    )
    list_select_related = (
        "owner",
        "patient",
        "communication",
        "appointment",
    )
