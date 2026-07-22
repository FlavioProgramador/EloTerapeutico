"""QuerySets de recursos auxiliares de scheduling."""

from apps.scheduling.models import (
    AppointmentRecurrence,
    AppointmentReminder,
    PackageSession,
    PatientPackage,
    Room,
    ScheduleBlock,
    TelemedicineRoom,
)


def schedule_blocks_queryset():
    return ScheduleBlock.objects.select_related("therapist", "created_by")


def rooms_queryset():
    return Room.objects.select_related("therapist")


def patient_packages_queryset():
    return PatientPackage.objects.select_related(
        "patient",
        "therapist",
        "created_by",
    ).prefetch_related("package_sessions__appointment")


def package_sessions_queryset():
    return PackageSession.objects.select_related(
        "package",
        "package__therapist",
        "appointment",
    )


def recurrences_queryset():
    return AppointmentRecurrence.objects.select_related(
        "patient",
        "therapist",
        "room",
    ).prefetch_related("appointments")


def telemedicine_rooms_queryset():
    return TelemedicineRoom.objects.select_related(
        "organization",
        "organization__settings",
        "appointment",
        "appointment__patient",
        "appointment__therapist",
    ).prefetch_related(
        "invitations",
        "participant_sessions",
    )


def appointment_reminders_queryset():
    return AppointmentReminder.objects.select_related(
        "appointment",
        "appointment__therapist",
    )


__all__ = [
    "appointment_reminders_queryset",
    "package_sessions_queryset",
    "patient_packages_queryset",
    "recurrences_queryset",
    "rooms_queryset",
    "schedule_blocks_queryset",
    "telemedicine_rooms_queryset",
]
