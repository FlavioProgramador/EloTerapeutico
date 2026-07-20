"""Fronteira entre o domínio financeiro e scheduling."""

from __future__ import annotations

from apps.scheduling.models import Appointment, PatientPackage


def eligible_appointments_for_charge(*, actor, appointment_ids, for_update: bool = False):
    queryset = Appointment.objects.filter(
        id__in=appointment_ids,
        therapist=actor,
        status__in=[Appointment.Status.CONFIRMED, Appointment.Status.COMPLETED],
    ).select_related("patient").order_by("id")
    return queryset.select_for_update() if for_update else queryset


def unbilled_appointments_for(*, actor):
    if not actor or actor.is_anonymous or not actor.is_therapist:
        return Appointment.objects.none()
    return (
        Appointment.objects.filter(
            therapist=actor,
            status=Appointment.Status.CONFIRMED,
        )
        .exclude(financial_transactions__isnull=False)
        .select_related("patient")
        .order_by("-start_time")
    )


def confirm_appointment_after_payment(*, appointment_id: int | None) -> None:
    if not appointment_id:
        return
    Appointment.objects.filter(
        pk=appointment_id, status=Appointment.Status.SCHEDULED
    ).update(status=Appointment.Status.CONFIRMED)


def package_financial_payload(*, package: PatientPackage) -> dict:
    return {
        "therapist": package.therapist,
        "patient": package.patient,
        "amount": package.total_value,
        "due_date": package.valid_from,
        "description": f"Pacote {package.name}",
    }


__all__ = [
    "confirm_appointment_after_payment",
    "eligible_appointments_for_charge",
    "package_financial_payload",
    "unbilled_appointments_for",
]
