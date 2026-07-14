"""Serviços transacionais do domínio de agenda."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from apps.agenda.models import (
    Appointment,
    AppointmentRecurrence,
    AppointmentReminder,
    PackageSession,
    PatientPackage,
    TelemedicineRoom,
)
from apps.core.exceptions import AuthorizationError, DomainIntegrityError


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
            rule.frequency == AppointmentRecurrence.Frequency.CUSTOM and weekdays and current.weekday() not in weekdays
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


def mask_phone(value: str) -> str:
    digits = "".join(char for char in (value or "") if char.isdigit())
    return f"***{digits[-4:]}" if len(digits) >= 4 else "não informado"


def create_appointment_resources(
    appointment: Appointment,
    *,
    send_whatsapp_reminder: bool = False,
    package: PatientPackage | None = None,
) -> None:
    """Cria recursos derivados sem realizar envio externo na requisição."""
    if package:
        if package.patient_id != appointment.patient_id or package.therapist_id != appointment.therapist_id:
            raise AuthorizationError(
                "O pacote não pertence ao paciente e profissional informados.",
                code="agenda_package_access_denied",
                field="package",
            )
        package.consume()
        PackageSession.objects.create(
            package=package,
            appointment=appointment,
            scheduled_for=appointment.start_time,
            status=PackageSession.Status.SCHEDULED,
            consumed=True,
        )

    if appointment.modality in {
        Appointment.Modality.ONLINE,
        Appointment.Modality.HYBRID,
    }:
        TelemedicineRoom.objects.get_or_create(
            appointment=appointment,
            defaults={
                "expires_at": appointment.end_time + timedelta(hours=2),
                "status": TelemedicineRoom.Status.AVAILABLE,
            },
        )

    if send_whatsapp_reminder:
        phone = appointment.patient.whatsapp or appointment.patient.phone
        AppointmentReminder.objects.create(
            appointment=appointment,
            channel=AppointmentReminder.Channel.WHATSAPP,
            scheduled_for=max(appointment.start_time - timedelta(hours=24), timezone.now()),
            recipient_masked=mask_phone(phone),
        )


def release_package_session(appointment: Appointment) -> None:
    try:
        package_session = appointment.package_session
    except PackageSession.DoesNotExist:
        return

    if package_session.consumed and package_session.status not in {
        PackageSession.Status.COMPLETED,
        PackageSession.Status.MISSED,
    }:
        package_session.consumed = False
        package_session.status = PackageSession.Status.CANCELLED
        package_session.save(update_fields=["consumed", "status", "updated_at"])
        package_session.package.release()


def sync_package_session_status(appointment: Appointment) -> None:
    try:
        package_session = appointment.package_session
    except PackageSession.DoesNotExist:
        return

    mapping = {
        Appointment.Status.SCHEDULED: PackageSession.Status.SCHEDULED,
        Appointment.Status.CONFIRMED: PackageSession.Status.CONFIRMED,
        Appointment.Status.COMPLETED: PackageSession.Status.COMPLETED,
        Appointment.Status.MISSED: PackageSession.Status.MISSED,
        Appointment.Status.CANCELLED: PackageSession.Status.CANCELLED,
        Appointment.Status.RESCHEDULED: PackageSession.Status.RESCHEDULED,
    }
    package_session.status = mapping[appointment.status]
    package_session.save(update_fields=["status", "updated_at"])


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

    with transaction.atomic():
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
                raise DomainIntegrityError(
                    f"A recorrência possui conflito em {target_date:%d/%m/%Y}: {labels}.",
                    code="agenda_recurrence_conflict",
                    field="start_time",
                )

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
