"""Admin de consultas."""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from apps.scheduling.exceptions import CompletedAppointmentDeletionError
from apps.scheduling.models import Appointment
from apps.scheduling.services import cancel_appointment_for_deletion


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
    autocomplete_fields = (
        "patient",
        "therapist",
        "room",
        "recurrence",
        "package",
    )
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
            {
                "fields": ("notes", "cancellation_reason"),
                "classes": ("collapse",),
            },
        ),
        (
            "Auditoria",
            {
                "fields": (
                    "created_by",
                    "updated_by",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Cancelar agendamentos selecionados")
    def action_cancel_appointments(self, request, queryset):
        if not request.user.has_perm("agenda.change_appointment"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        protected = 0
        for appointment in queryset.exclude(status=Appointment.Status.CANCELLED):
            try:
                cancel_appointment_for_deletion(
                    actor=request.user,
                    appointment=appointment,
                )
            except CompletedAppointmentDeletionError:
                protected += 1
            else:
                count += 1
        self.message_user(
            request,
            f"{count} agendamento(s) cancelado(s); {protected} protegido(s).",
            messages.WARNING,
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(therapist=request.user)
        return queryset


__all__ = ["AppointmentAdmin"]
