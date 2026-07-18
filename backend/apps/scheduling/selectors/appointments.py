"""Selectors de consultas da Agenda."""

from django.db.models import QuerySet

from apps.scheduling.models import Appointment


def appointment_queryset(*, include_details: bool = False) -> QuerySet[Appointment]:
    queryset = Appointment.objects.select_related(
        "patient",
        "therapist",
        "room",
        "recurrence",
        "package",
        "telemedicine_room",
        "evolution",
        "evolution__clinical_data",
    )
    if include_details:
        queryset = queryset.prefetch_related("participants", "reminders")
    return queryset
