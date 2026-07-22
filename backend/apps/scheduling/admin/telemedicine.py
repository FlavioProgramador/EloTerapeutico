"""Admin seguro de telemedicina e lembretes."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.scheduling.models import (
    AppointmentReminder,
    TelemedicineConsent,
    TelemedicineInvitation,
    TelemedicineParticipantSession,
    TelemedicineRoom,
    TelemedicineWebhookEvent,
)


@admin.register(TelemedicineRoom)
class TelemedicineRoomAdmin(ModelAdmin):
    list_display = (
        "appointment",
        "provider",
        "status",
        "e2ee_enabled",
        "expires_at",
        "started_at",
        "ended_at",
    )
    list_filter = ("provider", "status", "e2ee_enabled", "expires_at")
    search_fields = (
        "public_id",
        "appointment__patient__full_name",
        "appointment__therapist__full_name",
    )
    list_select_related = (
        "organization",
        "appointment",
        "appointment__patient",
        "appointment__therapist",
    )
    raw_id_fields = ("appointment", "closed_by")
    exclude = (
        "patient_token",
        "professional_token",
        "e2ee_key",
        "provider_room_name",
        "provider_room_sid",
    )
    readonly_fields = (
        "organization",
        "public_id",
        "provider",
        "e2ee_enabled",
        "expires_at",
        "revoked_at",
        "started_at",
        "ended_at",
        "patient_joined_at",
        "professional_joined_at",
        "last_participant_left_at",
        "failure_code",
        "created_at",
        "updated_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TelemedicineInvitation)
class TelemedicineInvitationAdmin(ModelAdmin):
    list_display = (
        "room",
        "role",
        "expires_at",
        "revoked_at",
        "last_used_at",
        "use_count",
    )
    list_filter = ("role", "expires_at", "revoked_at")
    list_select_related = ("organization", "room", "created_by")
    raw_id_fields = ("room", "created_by")
    exclude = ("token_hash",)
    readonly_fields = (
        "organization",
        "role",
        "expires_at",
        "revoked_at",
        "last_used_at",
        "use_count",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TelemedicineConsent)
class TelemedicineConsentAdmin(ModelAdmin):
    list_display = (
        "room",
        "patient",
        "document_version",
        "acceptance_method",
        "accepted_at",
        "revoked_at",
    )
    list_filter = ("document_version", "acceptance_method", "accepted_at")
    list_select_related = ("organization", "room", "patient")
    raw_id_fields = ("room", "patient")
    exclude = ("document_hash",)
    readonly_fields = (
        "organization",
        "responsible_guardian_name",
        "document_version",
        "acceptance_method",
        "accepted_at",
        "revoked_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TelemedicineParticipantSession)
class TelemedicineParticipantSessionAdmin(ModelAdmin):
    list_display = (
        "room",
        "role",
        "joined_at",
        "left_at",
        "connection_aborted",
    )
    list_filter = ("role", "connection_aborted", "joined_at", "left_at")
    list_select_related = ("organization", "room")
    raw_id_fields = ("room",)
    exclude = (
        "provider_participant_identity",
        "provider_participant_sid",
    )
    readonly_fields = (
        "organization",
        "role",
        "joined_at",
        "left_at",
        "disconnect_reason",
        "connection_aborted",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TelemedicineWebhookEvent)
class TelemedicineWebhookEventAdmin(ModelAdmin):
    list_display = (
        "provider",
        "event_type",
        "room",
        "received_at",
        "processed_at",
        "processing_error",
    )
    list_filter = ("provider", "event_type", "received_at", "processed_at")
    list_select_related = ("room",)
    raw_id_fields = ("room",)
    exclude = ("provider_event_id", "payload_hash")
    readonly_fields = (
        "provider",
        "event_type",
        "occurred_at",
        "received_at",
        "processed_at",
        "processing_error",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(ModelAdmin):
    list_display = (
        "appointment",
        "channel",
        "scheduled_for",
        "status",
        "recipient_masked",
    )
    list_filter = ("channel", "status", "scheduled_for")
    search_fields = ("appointment__patient__full_name", "recipient_masked")
    list_select_related = ("appointment", "appointment__patient")
    raw_id_fields = ("appointment",)


__all__ = [
    "AppointmentReminderAdmin",
    "TelemedicineConsentAdmin",
    "TelemedicineInvitationAdmin",
    "TelemedicineParticipantSessionAdmin",
    "TelemedicineRoomAdmin",
    "TelemedicineWebhookEventAdmin",
]
