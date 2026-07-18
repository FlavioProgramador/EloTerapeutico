"""Casos de uso de pacotes e sessões vinculadas."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.agenda.models import Appointment, AppointmentRecurrence, PackageSession, PatientPackage
from apps.agenda.services.recurrences import generate_recurrence_appointments
from apps.agenda.services.resources import create_appointment_resources


@transaction.atomic
def create_patient_package(*, actor, validated_data: dict) -> PatientPackage:
    auto_schedule = validated_data.pop("auto_schedule", False)
    first_at = validated_data.pop("first_appointment_at", None)
    frequency = validated_data.pop("frequency", AppointmentRecurrence.Frequency.WEEKLY)
    weekdays = validated_data.pop("weekdays", [])
    duration = validated_data.pop("duration_minutes", 50)
    modality = validated_data.pop("modality", Appointment.Modality.IN_PERSON)
    appointment_type = validated_data.pop("appointment_type", Appointment.AppointmentType.PSYCHOTHERAPY)
    room = validated_data.pop("room", None)
    remind = validated_data.pop("send_whatsapp_reminder", False)
    validated_data["created_by"] = actor
    package = PatientPackage.objects.create(**validated_data)

    if package.generate_charge:
        from apps.financeiro.models import FinancialTransaction

        FinancialTransaction.objects.create(
            therapist=package.therapist,
            patient=package.patient,
            transaction_type=FinancialTransaction.TransactionType.INCOME,
            category=FinancialTransaction.Category.SUBSCRIPTION,
            amount=package.total_value,
            payment_status=FinancialTransaction.PaymentStatus.PENDING,
            due_date=package.valid_from,
            description=f"Pacote {package.name}",
        )

    if auto_schedule and first_at:
        rule = AppointmentRecurrence.objects.create(
            patient=package.patient,
            therapist=package.therapist,
            frequency=frequency,
            weekdays=weekdays,
            starts_on=first_at.date(),
            max_occurrences=package.sessions_contracted,
            start_time=timezone.localtime(first_at).time().replace(tzinfo=None),
            duration_minutes=duration,
            modality=modality,
            appointment_type=appointment_type,
            room=room,
            session_value=package.unit_value,
            created_by=actor,
        )
        conflicts = Appointment.conflict_details(
            therapist=package.therapist,
            patient=package.patient,
            start_time=first_at,
            end_time=first_at + timedelta(minutes=duration),
            room=room,
        )
        if any(conflicts.values()):
            raise ValidationError({"first_appointment_at": "A primeira sessão possui conflito."})
        first = Appointment.objects.create(
            patient=package.patient,
            therapist=package.therapist,
            start_time=first_at,
            end_time=first_at + timedelta(minutes=duration),
            modality=modality,
            appointment_type=appointment_type,
            room=room,
            session_value=package.unit_value,
            is_recurring=True,
            recurrence=rule,
            package=package,
            origin=Appointment.Origin.PACKAGE,
            created_by=actor,
            updated_by=actor,
        )
        create_appointment_resources(first, send_whatsapp_reminder=remind, package=package)
        generate_recurrence_appointments(
            rule,
            first_appointment=first,
            conflict_strategy="error",
            send_whatsapp_reminder=remind,
            package=package,
        )
    return package


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
