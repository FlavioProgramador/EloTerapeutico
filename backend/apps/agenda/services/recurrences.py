"""Casos de uso de recorrência da Agenda."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.agenda.models import Appointment, AppointmentRecurrence, PatientPackage
from apps.agenda.services.resources import create_appointment_resources


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def recurrence_dates(rule: AppointmentRecurrence, limit: int | None = None):
    """Gera datas da recorrência com limite defensivo."""
    max_items = min(limit or rule.max_occurrences or 12, 365)
    current = rule.starts_on
    produced = 0
    weekdays = sorted({int(day) for day in (rule.weekdays or []) if 0 <= int(day) <= 6})

    while produced < max_items:
        if rule.ends_on and current > rule.ends_on:
            break
        include = not (
            rule.frequency == AppointmentRecurrence.Frequency.CUSTOM
            and weekdays
            and current.weekday() not in weekdays
        )
        if include:
            yield current
            produced += 1

        if rule.frequency == AppointmentRecurrence.Frequency.MONTHLY:
            current = add_months(current, max(rule.interval, 1))
        elif rule.frequency == AppointmentRecurrence.Frequency.BIWEEKLY:
            current += timedelta(weeks=2 * max(rule.interval, 1))
        elif rule.frequency == AppointmentRecurrence.Frequency.CUSTOM and weekdays:
            current += timedelta(days=1)
        else:
            current += timedelta(weeks=max(rule.interval, 1))


def combine_local(rule: AppointmentRecurrence, target_date: date) -> datetime:
    tz = ZoneInfo(rule.timezone_name or "America/Sao_Paulo")
    return datetime.combine(target_date, rule.start_time, tzinfo=tz)


@transaction.atomic
def generate_recurrence_appointments(
    rule: AppointmentRecurrence,
    *,
    first_appointment: Appointment | None = None,
    conflict_strategy: str = "error",
    send_whatsapp_reminder: bool = False,
    package: PatientPackage | None = None,
) -> list[Appointment]:
    """Materializa ocorrências futuras de uma série dentro de uma transação."""
    created: list[Appointment] = []
    first_date = first_appointment.start_time.date() if first_appointment else None

    for target_date in recurrence_dates(rule):
        if first_date and target_date == first_date:
            continue
        start = combine_local(rule, target_date)
        end = start + timedelta(minutes=rule.duration_minutes)
        conflicts = Appointment.conflict_details(
            therapist=rule.therapist,
            patient=rule.patient,
            start_time=start,
            end_time=end,
            room=rule.room,
        )
        if any(conflicts.values()):
            if conflict_strategy == "skip":
                continue
            labels = ", ".join(key for key, value in conflicts.items() if value)
            raise ValidationError(f"A recorrência possui conflito em {target_date:%d/%m/%Y}: {labels}.")
        appointment = Appointment.objects.create(
            patient=rule.patient,
            therapist=rule.therapist,
            start_time=start,
            end_time=end,
            status=Appointment.Status.SCHEDULED,
            modality=rule.modality,
            appointment_type=rule.appointment_type,
            room=rule.room,
            session_value=rule.session_value,
            notes=rule.notes,
            origin=Appointment.Origin.RECURRENCE,
            is_recurring=True,
            recurrence=rule,
            recurrence_rule={
                AppointmentRecurrence.Frequency.WEEKLY: Appointment.RecurrenceRule.WEEKLY,
                AppointmentRecurrence.Frequency.BIWEEKLY: Appointment.RecurrenceRule.BIWEEKLY,
                AppointmentRecurrence.Frequency.MONTHLY: Appointment.RecurrenceRule.MONTHLY,
            }.get(rule.frequency, Appointment.RecurrenceRule.WEEKLY),
            parent_appointment=first_appointment,
            package=package,
            created_by=rule.created_by,
            updated_by=rule.created_by,
        )
        if first_appointment is not None:
            appointment.participants.set(first_appointment.participants.all())
        create_appointment_resources(
            appointment,
            send_whatsapp_reminder=send_whatsapp_reminder,
            package=package,
        )
        created.append(appointment)
    return created
