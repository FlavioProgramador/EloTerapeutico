from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import (
    Communication,
    CommunicationAttempt,
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationChannelConfig,
    CommunicationPlanEntitlement,
    CommunicationPreference,
    CommunicationRecipient,
    CommunicationTemplate,
    InAppNotification,
    InboundMessage,
    PublicCommunicationActionToken,
)


class ReadOnlyHistoryAdmin(ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Communication)
class CommunicationAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "owner", "patient", "channel", "category", "status_badge", "scheduled_at", "created_at")
    list_filter = ("channel", "category", "status", "priority", "created_at")
    search_fields = ("id", "public_id", "subject", "owner__email", "patient__full_name", "source_event")
    readonly_fields = tuple(field.name for field in Communication._meta.fields)
    list_select_related = ("owner", "patient", "appointment", "created_by")
    date_hierarchy = "created_at"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {Communication.Status.DELIVERED: "#15803d", Communication.Status.SENT: "#0369a1", Communication.Status.FAILED: "#b91c1c", Communication.Status.SCHEDULED: "#a16207", Communication.Status.QUEUED: "#6d28d9"}
        return format_html('<span style="background:{};color:white;padding:3px 8px;border-radius:999px">{}</span>', colors.get(obj.status, "#475569"), obj.get_status_display())


@admin.register(CommunicationRecipient)
class CommunicationRecipientAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "communication", "recipient_type", "name", "destination_masked", "channel", "status")
    list_filter = ("recipient_type", "channel", "status")
    search_fields = ("communication__id", "name", "destination_masked")
    readonly_fields = tuple(field.name for field in CommunicationRecipient._meta.fields)
    list_select_related = ("communication", "patient")


@admin.register(CommunicationAttempt)
class CommunicationAttemptAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "communication", "attempt_number", "provider", "status", "started_at", "finished_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("communication__id", "external_id", "error_code")
    readonly_fields = tuple(field.name for field in CommunicationAttempt._meta.fields)
    list_select_related = ("communication", "recipient")


@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(ModelAdmin):
    list_display = ("name", "owner", "channel", "category", "is_system_template", "is_active", "is_archived")
    list_filter = ("channel", "category", "is_system_template", "is_active", "is_archived")
    search_fields = ("name", "slug", "description", "owner__email")
    readonly_fields = ("allowed_variables", "is_system_template", "created_at", "updated_at")
    list_select_related = ("owner", "created_by", "updated_by")


@admin.register(CommunicationAutomation)
class CommunicationAutomationAdmin(ModelAdmin):
    list_display = ("name", "owner", "event_type", "channel", "template", "is_active", "updated_at")
    list_filter = ("event_type", "channel", "is_active")
    search_fields = ("name", "description", "owner__email")
    list_select_related = ("owner", "template", "created_by", "updated_by")


@admin.register(CommunicationAutomationRun)
class CommunicationAutomationRunAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "automation", "source_event", "status", "communication", "started_at", "finished_at")
    list_filter = ("status", "source_event", "started_at")
    search_fields = ("automation__name", "source_object_id", "idempotency_key")
    readonly_fields = tuple(field.name for field in CommunicationAutomationRun._meta.fields)
    list_select_related = ("automation", "communication")


@admin.register(CommunicationPreference)
class CommunicationPreferenceAdmin(ModelAdmin):
    list_display = ("patient", "owner", "preferred_channel", "general_opt_out", "allow_email", "allow_whatsapp", "updated_at")
    list_filter = ("preferred_channel", "general_opt_out", "allow_email", "allow_whatsapp", "allow_sms")
    search_fields = ("patient__full_name", "owner__email")
    list_select_related = ("owner", "patient", "consent_recorded_by")


@admin.register(InAppNotification)
class InAppNotificationAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "recipient", "title", "notification_type", "priority", "is_read", "created_at")
    list_filter = ("notification_type", "priority", "is_read", "created_at")
    search_fields = ("title", "recipient__email")
    readonly_fields = tuple(field.name for field in InAppNotification._meta.fields)
    list_select_related = ("owner", "recipient", "communication")


@admin.register(InboundMessage)
class InboundMessageAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "owner", "sender_masked", "channel", "provider", "status", "received_at")
    list_filter = ("channel", "provider", "status", "received_at")
    search_fields = ("sender_masked", "external_id", "owner__email")
    readonly_fields = tuple(field.name for field in InboundMessage._meta.fields)
    list_select_related = ("owner", "patient", "communication", "reviewed_by")


@admin.register(CommunicationChannelConfig)
class CommunicationChannelConfigAdmin(ModelAdmin):
    list_display = (
        "owner",
        "channel",
        "provider",
        "is_active",
        "connection_status",
        "credential_summary",
        "last_tested_at",
        "last_validated_at",
    )
    list_filter = ("channel", "provider", "is_active", "connection_status")
    search_fields = ("owner__email", "sender", "public_identifier", "last_error_code")
    readonly_fields = (
        "credential_summary",
        "last_tested_at",
        "last_validated_at",
        "last_error_code",
        "last_error_message",
        "created_at",
        "updated_at",
    )
    exclude = ("credentials",)
    list_select_related = ("owner",)

    @admin.display(description="Credenciais")
    def credential_summary(self, obj):
        configured = sorted(key for key, value in obj.get_credentials().items() if value)
        return ", ".join(configured) if configured else "Nenhum segredo armazenado"


@admin.register(PublicCommunicationActionToken)
class PublicCommunicationActionTokenAdmin(ReadOnlyHistoryAdmin):
    list_display = ("id", "owner", "purpose", "patient", "appointment", "expires_at", "used_at", "revoked_at")
    list_filter = ("purpose", "expires_at", "used_at", "revoked_at")
    search_fields = ("owner__email", "patient__full_name", "appointment__id")
    exclude = ("token_hash",)
    readonly_fields = tuple(field.name for field in PublicCommunicationActionToken._meta.fields if field.name != "token_hash")
    list_select_related = ("owner", "patient", "communication", "appointment")


@admin.register(CommunicationPlanEntitlement)
class CommunicationPlanEntitlementAdmin(ModelAdmin):
    list_display = ("plan", "communications_enabled", "email_enabled", "automations_enabled", "max_communications_per_month", "max_automations")
    list_filter = ("communications_enabled", "email_enabled", "automations_enabled", "whatsapp_enabled", "sms_enabled")
    search_fields = ("plan__name", "plan__slug")
    list_select_related = ("plan",)
