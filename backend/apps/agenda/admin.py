"""Administração do domínio de Agenda."""

from django.contrib import admin

from .models import (
    Appointment,
    AppointmentRecurrence,
    AppointmentReminder,
    PackageSession,
    PatientPackage,
    Room,
    ScheduleBlock,
    TelemedicineRoom,
)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "therapist",
        "start_time",
        "duration_display",
        "modality",
        "appointment_type",
        "room",
        "status",
        "session_value",
    )
    list_filter = (
        "status",
        "modality",
        "appointment_type",
        "therapist",
        "room",
        "is_recurring",
        ("start_time", admin.DateFieldListFilter),
    )
    search_fields = (
        "patient__full_name",
        "patient__social_name",
        "therapist__full_name",
        "notes",
    )
    list_select_related = (
        "patient",
        "therapist",
        "room",
        "recurrence",
        "package",
    )
    readonly_fields = ("duration_minutes", "created_at", "updated_at")
    date_hierarchy = "start_time"
    ordering = ("-start_time",)


@admin.register(AppointmentRecurrence)
class AppointmentRecurrenceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient",
        "therapist",
        "frequency",
        "start_time",
        "starts_on",
        "ends_on",
        "status",
    )
    list_filter = ("status", "frequency", "therapist")
    search_fields = ("patient__full_name", "therapist__full_name")


@admin.register(ScheduleBlock)
class ScheduleBlockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "therapist",
        "start_time",
        "end_time",
        "reason",
        "is_active",
    )
    list_filter = ("reason", "is_active", "therapist")
    date_hierarchy = "start_time"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "therapist", "location", "capacity", "is_active")
    list_filter = ("is_active", "therapist")
    search_fields = ("name", "location", "therapist__full_name")


@admin.register(PatientPackage)
class PatientPackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "patient",
        "therapist",
        "sessions_used",
        "sessions_contracted",
        "valid_until",
        "status",
    )
    list_filter = ("status", "therapist")
    search_fields = ("name", "patient__full_name")


@admin.register(PackageSession)
class PackageSessionAdmin(admin.ModelAdmin):
    list_display = (
        "package",
        "appointment",
        "scheduled_for",
        "status",
        "consumed",
    )
    list_filter = ("status", "consumed")


@admin.register(TelemedicineRoom)
class TelemedicineRoomAdmin(admin.ModelAdmin):
    list_display = ("appointment", "status", "expires_at", "revoked_at")
    list_filter = ("status",)
    readonly_fields = (
        "patient_token",
        "professional_token",
        "created_at",
        "updated_at",
    )


@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = (
        "appointment",
        "channel",
        "scheduled_for",
        "status",
        "recipient_masked",
    )
    list_filter = ("channel", "status")
