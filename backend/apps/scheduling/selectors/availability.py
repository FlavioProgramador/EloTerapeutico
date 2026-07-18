"""Cálculo somente leitura de horários disponíveis."""

from datetime import datetime, timedelta

from django.utils import timezone

from apps.patients.models import Patient
from apps.scheduling.models import Appointment, Room
from apps.users.models import PracticeSettings, WorkingHours


def available_slots(*, therapist, target_date, duration: int, patient_id=None, room_id=None) -> list[dict[str, str]]:
    working = WorkingHours.objects.filter(
        therapist=therapist,
        weekday=target_date.weekday(),
        is_active=True,
    ).first()
    if not working:
        return []

    tz = timezone.get_current_timezone()
    current = timezone.make_aware(datetime.combine(target_date, working.start_time), tz)
    day_end = timezone.make_aware(datetime.combine(target_date, working.end_time), tz)
    patient = Patient.objects.filter(pk=patient_id, therapist=therapist, deleted_at__isnull=True).first()
    room = Room.objects.filter(pk=room_id, therapist=therapist, is_active=True).first()
    slots: list[dict[str, str]] = []
    practice = PracticeSettings.objects.filter(user=therapist).first()
    interval = practice.appointment_interval_minutes if practice else 0
    minimum_start = timezone.now() + timedelta(hours=practice.minimum_booking_notice_hours if practice else 0)

    while current + timedelta(minutes=duration) <= day_end:
        end = current + timedelta(minutes=duration)
        conflicts = Appointment.conflict_details(
            therapist=therapist,
            patient=patient,
            start_time=current,
            end_time=end,
            room=room,
        )
        if (
            current >= minimum_start
            and (bool(practice and practice.allow_overbooking) or not conflicts["therapist"])
            and not conflicts["room"]
            and not conflicts["block"]
            and (not patient or not conflicts["patient"])
        ):
            slots.append(
                {
                    "start": current.strftime("%H:%M"),
                    "end": end.strftime("%H:%M"),
                    "start_datetime": current.isoformat(),
                    "end_datetime": end.isoformat(),
                }
            )
        current = end + timedelta(minutes=interval)
    return slots
