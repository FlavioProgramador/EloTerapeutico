"""Consultas somente leitura para detectar conflitos de agendamento."""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from apps.scheduling.models import Appointment, ScheduleBlock


@dataclass(frozen=True, slots=True)
class AppointmentConflictResult:
    therapist: bool
    patient: bool
    room: bool
    schedule_block: bool

    @property
    def has_conflict(self) -> bool:
        return any(self.as_dict().values())

    def as_dict(self) -> dict[str, bool]:
        return {
            "therapist": self.therapist,
            "patient": self.patient,
            "room": self.room,
            "block": self.schedule_block,
        }


def get_appointment_conflicts(
    *,
    therapist,
    patient,
    start_time,
    end_time,
    room=None,
    participants=None,
    exclude_appointment_id=None,
) -> AppointmentConflictResult:
    """Retorna conflitos por recurso sem alterar estado."""

    base = Appointment.objects.filter(
        status__in=(Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED),
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    if exclude_appointment_id:
        base = base.exclude(pk=exclude_appointment_id)

    participant_ids = [getattr(item, "pk", item) for item in (participants or [])]
    patient_query = Q()
    has_patient_filter = patient is not None or bool(participant_ids)
    if patient is not None:
        patient_query = Q(patient=patient) | Q(participants=patient)
    if participant_ids:
        patient_query |= Q(patient_id__in=participant_ids) | Q(
            participants__id__in=participant_ids
        )

    return AppointmentConflictResult(
        therapist=base.filter(therapist=therapist).exists(),
        patient=(
            has_patient_filter
            and base.filter(patient_query).distinct().exists()
        ),
        room=bool(room and base.filter(room=room).exists()),
        schedule_block=ScheduleBlock.objects.filter(
            therapist=therapist,
            start_time__lt=end_time,
            end_time__gt=start_time,
            is_active=True,
        ).exists(),
    )


__all__ = ["AppointmentConflictResult", "get_appointment_conflicts"]
