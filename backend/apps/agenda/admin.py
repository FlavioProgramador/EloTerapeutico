"""Administração do domínio de Agenda."""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin

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
class AppointmentAdmin(ModelAdmin):
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
        "origin",
        ("start_time", admin.DateFieldListFilter),
    )
    search_fields = (
        "patient__full_name",
        "patient__social_name",
        "therapist__full_name",
        "therapist__email",
        "notes",
    )
    list_select_related = (
        "patient",
        "therapist",
        "room",
        "recurrence",
        "package",
    )
    autocomplete_fields = ("patient", "therapist", "room", "recurrence", "package")
    raw_id_fields = ("parent_appointment",)
    filter_horizontal = ("participants",)
    readonly_fields = ("duration_minutes", "created_at", "updated_at")
    date_hierarchy = "start_time"
    ordering = ("-start_time",)
    actions = ("action_cancel_appointments",)

    fieldsets = (
        (
            "Paciente e profissional",
            {"fields": ("patient", "participants", "therapist")},
        ),
        (
            "Agenda",
            {
                "fields": (
                    "start_time",
                    "end_time",
                    "duration_minutes",
                    "status",
                    "modality",
                    "appointment_type",
                    "room",
                    "session_value",
                )
            },
        ),
        (
            "Recorrência e pacote",
            {
                "fields": (
                    "origin",
                    "is_recurring",
                    "recurrence_rule",
                    "recurrence",
                    "parent_appointment",
                    "package",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Observações",
            {"fields": ("notes", "cancellation_reason"), "classes": ("collapse",)},
        ),
        (
            "Auditoria",
            {
                "fields": ("created_by", "updated_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Cancelar agendamentos selecionados")
    def action_cancel_appointments(self, request, queryset):
        if not request.user.has_perm("agenda.change_appointment"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        updated = queryset.exclude(status=Appointment.Status.CANCELLED).update(
            status=Appointment.Status.CANCELLED
        )
        self.message_user(request, f"{updated} agendamento(s) cancelado(s).", messages.WARNING)


@admin.register(AppointmentRecurrence)
class AppointmentRecurrenceAdmin(ModelAdmin):
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
    search_fields = ("patient__full_name", "therapist__full_name", "therapist__email")
    list_select_related = ("patient", "therapist")
    autocomplete_fields = ("patient", "therapist")


@admin.register(ScheduleBlock)
class ScheduleBlockAdmin(ModelAdmin):
    list_display = (
        "id",
        "therapist",
        "start_time",
        "end_time",
        "reason",
        "is_active",
    )
    list_filter = ("reason", "is_active", "therapist")
    search_fields = ("therapist__full_name", "therapist__email", "notes")
    list_select_related = ("therapist",)
    autocomplete_fields = ("therapist",)
    date_hierarchy = "start_time"


@admin.register(Room)
class RoomAdmin(ModelAdmin):
    list_display = ("name", "therapist", "location", "capacity", "is_active")
    list_filter = ("is_active", "therapist")
    search_fields = ("name", "location", "therapist__full_name")
    list_select_related = ("therapist",)
    autocomplete_fields = ("therapist",)


@admin.register(PatientPackage)
class PatientPackageAdmin(ModelAdmin):
    list_display = (
        "name",
        "patient",
        "therapist",
        "sessions_used",
        "sessions_contracted",
        "valid_until",
        "status",
    )
    list_filter = ("status", "therapist", "valid_until")
    search_fields = ("name", "patient__full_name", "therapist__full_name")
    list_select_related = ("patient", "therapist")
    autocomplete_fields = ("patient", "therapist")


@admin.register(PackageSession)
class PackageSessionAdmin(ModelAdmin):
    list_display = (
        "package",
        "appointment",
        "scheduled_for",
        "status",
        "consumed",
    )
    list_filter = ("status", "consumed", "scheduled_for")
    search_fields = ("package__name", "appointment__patient__full_name")
    list_select_related = ("package", "appointment")
    raw_id_fields = ("appointment",)


@admin.register(TelemedicineRoom)
class TelemedicineRoomAdmin(ModelAdmin):
    list_display = ("appointment", "status", "expires_at", "revoked_at")
    list_filter = ("status", "expires_at")
    search_fields = ("appointment__patient__full_name",)
    list_select_related = ("appointment", "appointment__patient")
    raw_id_fields = ("appointment",)
    readonly_fields = (
        "patient_token",
        "professional_token",
        "created_at",
        "updated_at",
    )


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
