"""Admin de recorrências."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.scheduling.models import AppointmentRecurrence


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
    search_fields = (
        "patient__full_name",
        "therapist__full_name",
        "therapist__email",
    )
    list_select_related = ("patient", "therapist")
    autocomplete_fields = ("patient", "therapist")


__all__ = ["AppointmentRecurrenceAdmin"]
