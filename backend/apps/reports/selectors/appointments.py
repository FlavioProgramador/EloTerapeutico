"""Selectors de consultas usadas por relatórios de agenda."""

from datetime import date

from django.db.models import QuerySet

from apps.scheduling.models import Appointment


def appointments_for_period(*, owner, start: date, end: date) -> QuerySet[Appointment]:
    return (
        Appointment.objects.filter(
            therapist=owner,
            start_time__date__range=(start, end),
        )
        .select_related("patient", "therapist", "room")
        .prefetch_related("financial_transactions")
    )
