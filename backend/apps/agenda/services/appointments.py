"""Casos de uso transacionais de consultas."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.agenda.exceptions import CompletedAppointmentDeletionError
from apps.agenda.models import (
    Appointment,
    AppointmentRecurrence,
    PackageSession,
    PatientPackage,
    TelemedicineRoom,
)
from apps.agenda.services.financial_sync import cancel_financial_transaction, create_financial_transaction
from apps.agenda.services.packages import release_package_session, sync_package_session_status
from apps.agenda.services.recurrences import generate_recurrence_appointments
from apps.agenda.services.resources import create_appointment_resources

User = get_user_model()


def _raise_conflict_error(conflicts: dict[str, bool]) -> None:
    if not any(conflicts.values()):
        return
    labels = {
        "therapist": "profissional",
        "patient": "paciente",
        "room": "sala",
        "block": "bloqueio de agenda",
    }
    active = [labels[key] for key, value in conflicts.items() if value]
    raise ValidationError({"start_time": f"Conflito de horário com: {', '.join(active)}."})


def _validate_locked_conflicts(
    *,
    therapist,
    patient,
    participants,
    start,
    end,
    room,
    exclude_id=None,
) -> None:
    conflicts = Appointment.conflict_details(
        therapist=therapist,
        patient=patient,
        start_time=start,
        end_time=end,
        room=room,
        participants=participants,
        exclude_id=exclude_id,
    )
    _raise_conflict_error(conflicts)


@transaction.atomic
def create_appointment(*, actor, validated_data: dict) -> Appointment:
    participants = validated_data.pop("participants", [])
    remind = validated_data.pop("send_whatsapp_reminder", False)
    frequency = validated_data.pop("recurrence_frequency", None)
    interval = validated_data.pop("recurrence_interval", 1)
    weekdays = validated_data.pop("recurrence_weekdays", [])
    ends_on = validated_data.pop("recurrence_ends_on", None)
    max_occurrences = validated_data.pop("recurrence_max_occurrences", None)
    conflict_strategy = validated_data.pop("recurrence_conflict_strategy", "error")
    package = validated_data.get("package")
    validated_data["created_by"] = actor
    validated_data["updated_by"] = actor

    therapist = User.objects.select_for_update().get(pk=validated_data["therapist"].pk)
    validated_data["therapist"] = therapist
    if package:
        package = PatientPackage.objects.select_for_update().get(pk=package.pk)
        if not package.can_consume():
            raise ValidationError({"package": "O pacote está sem saldo, expirado ou inativo."})
        validated_data["package"] = package

    _validate_locked_conflicts(
        therapist=therapist,
        patient=validated_data["patient"],
        participants=participants,
        start=validated_data["start_time"],
        end=validated_data["end_time"],
        room=validated_data.get("room"),
    )

    recurrence = None
    if validated_data.get("is_recurring"):
        local_start = timezone.localtime(validated_data["start_time"])
        recurrence = AppointmentRecurrence.objects.create(
            patient=validated_data["patient"],
            therapist=validated_data["therapist"],
            frequency=frequency,
            interval=interval,
            weekdays=weekdays,
            starts_on=local_start.date(),
            ends_on=ends_on,
            max_occurrences=max_occurrences or 12,
            start_time=local_start.time().replace(tzinfo=None),
            duration_minutes=int((validated_data["end_time"] - validated_data["start_time"]).total_seconds() // 60),
            timezone_name=str(timezone.get_current_timezone()),
            modality=validated_data.get("modality", Appointment.Modality.IN_PERSON),
            appointment_type=validated_data.get(
                "appointment_type",
                Appointment.AppointmentType.PSYCHOTHERAPY,
            ),
            room=validated_data.get("room"),
            session_value=validated_data["session_value"],
            notes=validated_data.get("notes", ""),
            created_by=actor,
        )
        validated_data["recurrence"] = recurrence
        validated_data["origin"] = Appointment.Origin.RECURRENCE

    appointment = Appointment.objects.create(**validated_data)
    appointment.participants.set(participants)
    create_appointment_resources(
        appointment,
        send_whatsapp_reminder=remind,
        package=package,
    )
    if recurrence:
        generate_recurrence_appointments(
            recurrence,
            first_appointment=appointment,
            conflict_strategy=conflict_strategy,
            send_whatsapp_reminder=remind,
            package=package,
        )
    return appointment


@transaction.atomic
def update_appointment(*, actor, appointment: Appointment, validated_data: dict) -> Appointment:
    appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
    participants = validated_data.pop("participants", None)
    effective_participants = participants if participants is not None else list(appointment.participants.all())
    therapist = validated_data.get("therapist", appointment.therapist)
    therapist = User.objects.select_for_update().get(pk=therapist.pk)
    validated_data["therapist"] = therapist
    validated_data.pop("updated_by", None)

    _validate_locked_conflicts(
        therapist=therapist,
        patient=validated_data.get("patient", appointment.patient),
        participants=effective_participants,
        start=validated_data.get("start_time", appointment.start_time),
        end=validated_data.get("end_time", appointment.end_time),
        room=validated_data.get("room", appointment.room),
        exclude_id=appointment.pk,
    )

    for field, value in validated_data.items():
        setattr(appointment, field, value)
    appointment.updated_by = actor
    appointment.save()
    if participants is not None:
        appointment.participants.set(participants)
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
    if appointment.origin == Appointment.Origin.RESCHEDULE:
        try:
            package_session = appointment.package_session
        except PackageSession.DoesNotExist:
            package_session = None
        if package_session:
            package_session.scheduled_for = appointment.start_time
            package_session.status = PackageSession.Status.RESCHEDULED
            package_session.save(update_fields=["scheduled_for", "status", "updated_at"])
    return appointment


@transaction.atomic
def update_appointment_status(*, actor, appointment: Appointment, validated_data: dict) -> Appointment:
    appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
    new_status = validated_data.get("status", appointment.status)
    cancellation_reason = validated_data.get("cancellation_reason", appointment.cancellation_reason)
    if appointment.status == Appointment.Status.CANCELLED:
        raise ValidationError({"status": "Uma consulta cancelada não pode ser reativada diretamente."})
    if appointment.status in {Appointment.Status.COMPLETED, Appointment.Status.MISSED}:
        raise ValidationError({"status": "Uma sessão finalizada não pode voltar para um estado anterior."})
    if new_status == Appointment.Status.CANCELLED and not (cancellation_reason or "").strip():
        raise ValidationError({"cancellation_reason": "Informe o motivo do cancelamento."})

    appointment.status = new_status
    appointment.cancellation_reason = cancellation_reason
    appointment.updated_by = actor
    appointment.save(update_fields=["status", "cancellation_reason", "updated_by", "updated_at"])
    sync_package_session_status(appointment)
    if new_status == Appointment.Status.CONFIRMED:
        create_financial_transaction(appointment=appointment)
    elif new_status == Appointment.Status.CANCELLED:
        release_package_session(appointment)
        cancel_financial_transaction(appointment=appointment)
        try:
            appointment.telemedicine_room.revoke()
        except TelemedicineRoom.DoesNotExist:
            pass
    return appointment


@transaction.atomic
def cancel_appointment_for_deletion(*, actor, appointment: Appointment) -> Appointment:
    appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
    if appointment.status == Appointment.Status.COMPLETED:
        raise CompletedAppointmentDeletionError("Consultas realizadas não podem ser excluídas.")
    appointment.status = Appointment.Status.CANCELLED
    appointment.cancellation_reason = "Cancelada por exclusão administrativa."
    appointment.updated_by = actor
    appointment.save(update_fields=["status", "cancellation_reason", "updated_by", "updated_at"])
    release_package_session(appointment)
    cancel_financial_transaction(appointment=appointment)
    return appointment
