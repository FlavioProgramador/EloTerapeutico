"""Admin de telemedicina e lembretes."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.scheduling.models import AppointmentReminder, TelemedicineRoom


@admin.register(TelemedicineRoom)
class TelemedicineRoomAdmin(ModelAdmin):
    list_display = ("appointment", "status", "expires_at", "revoked_at")
    list_filter = ("status", "expires_at")
    search_fields = ("appointment__patient__full_name",)
    list_select_related = ("appointment", "appointment__patient")
    raw_id_fields = ("appointment",)
    readonly_fields = ("created_at", "updated_at")


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


__all__ = ["AppointmentReminderAdmin", "TelemedicineRoomAdmin"]
