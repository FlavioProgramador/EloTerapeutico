"""Casos de uso de recorrência da Agenda."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.scheduling.exceptions import InvalidRecurrenceScopeError, RecurrenceConflictError
from apps.scheduling.models import Appointment, AppointmentRecurrence, PatientPackage, Room
from apps.scheduling.services.resources import create_appointment_resources


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


def as_time(value):
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    return value


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


@transaction.atomic
def set_recurrence_status(
    *,
    recurrence: AppointmentRecurrence,
    status: str,
) -> AppointmentRecurrence:
    recurrence = AppointmentRecurrence.objects.select_for_update().get(pk=recurrence.pk)
    recurrence.status = status
    recurrence.save(update_fields=["status", "updated_at"])
    return recurrence


@transaction.atomic
def end_recurrence(
    *,
    recurrence: AppointmentRecurrence,
    ends_on: date | None = None,
) -> AppointmentRecurrence:
    recurrence = AppointmentRecurrence.objects.select_for_update().get(pk=recurrence.pk)
    recurrence.status = AppointmentRecurrence.Status.ENDED
    recurrence.ends_on = ends_on or timezone.localdate()
    recurrence.save(update_fields=["status", "ends_on", "updated_at"])
    recurrence.appointments.filter(
        start_time__date__gt=recurrence.ends_on,
        status__in=[
            Appointment.Status.SCHEDULED,
            Appointment.Status.CONFIRMED,
        ],
    ).update(
        status=Appointment.Status.CANCELLED,
        cancellation_reason="Recorrência encerrada.",
    )
    return recurrence


@transaction.atomic
def apply_bulk_recurrence_change(
    *,
    actor,
    recurrence: AppointmentRecurrence,
    occurrence: Appointment,
    scope: str,
    changes: dict,
) -> AppointmentRecurrence:
    if scope not in {"following", "all"}:
        raise InvalidRecurrenceScopeError("Escopo inválido.")

    recurrence = AppointmentRecurrence.objects.select_for_update().get(pk=recurrence.pk)
    occurrence = recurrence.appointments.select_for_update().get(pk=occurrence.pk)
    target_rule = recurrence

    if scope == "following":
        target_rule = AppointmentRecurrence.objects.create(
            patient=recurrence.patient,
            therapist=recurrence.therapist,
            frequency=changes.get("frequency", recurrence.frequency),
            interval=changes.get("interval", recurrence.interval),
            weekdays=changes.get("weekdays", recurrence.weekdays),
            starts_on=occurrence.start_time.date(),
            ends_on=changes.get("ends_on", recurrence.ends_on),
            max_occurrences=recurrence.max_occurrences,
            start_time=as_time(changes.get("start_time", recurrence.start_time)),
            duration_minutes=changes.get("duration_minutes", recurrence.duration_minutes),
            timezone_name=recurrence.timezone_name,
            modality=changes.get("modality", recurrence.modality),
            appointment_type=changes.get("appointment_type", recurrence.appointment_type),
            room_id=changes.get("room", recurrence.room_id),
            session_value=changes.get("session_value", recurrence.session_value),
            notes=changes.get("notes", recurrence.notes),
            created_by=actor,
        )
        recurrence.ends_on = occurrence.start_time.date() - timedelta(days=1)
        recurrence.save(update_fields=["ends_on", "updated_at"])

    editable = recurrence.appointments.select_for_update().filter(
        status__in=[
            Appointment.Status.SCHEDULED,
            Appointment.Status.CONFIRMED,
        ]
    )
    if scope == "following":
        editable = editable.filter(start_time__gte=occurrence.start_time)

    for item in editable:
        local = timezone.localtime(item.start_time)
        new_time = as_time(changes.get("start_time"))
        effective_time = new_time or target_rule.start_time
        new_start = local.replace(
            hour=effective_time.hour,
            minute=effective_time.minute,
            second=0,
            microsecond=0,
        )
        duration = int(changes.get("duration_minutes", target_rule.duration_minutes))
        room_id = changes.get("room", target_rule.room_id)
        conflicts = Appointment.conflict_details(
            therapist=target_rule.therapist,
            patient=target_rule.patient,
            start_time=new_start,
            end_time=new_start + timedelta(minutes=duration),
            room=Room.objects.filter(pk=room_id).first(),
            exclude_id=item.pk,
        )
        if any(conflicts.values()):
            raise RecurrenceConflictError(f"Conflito ao alterar ocorrência de {local:%d/%m/%Y}.")
        item.start_time = new_start
        item.end_time = new_start + timedelta(minutes=duration)
        item.room_id = room_id
        item.modality = changes.get("modality", target_rule.modality)
        item.appointment_type = changes.get("appointment_type", target_rule.appointment_type)
        item.recurrence = target_rule
        item.updated_by = actor
        item.save()

    for field in [
        "frequency",
        "interval",
        "weekdays",
        "ends_on",
        "duration_minutes",
        "modality",
        "appointment_type",
        "session_value",
        "notes",
    ]:
        if field in changes:
            setattr(target_rule, field, changes[field])
    if "start_time" in changes:
        target_rule.start_time = as_time(changes["start_time"])
    if "room" in changes:
        target_rule.room_id = changes["room"]
    target_rule.save()
    return target_rule
