"""Casos de uso de sessões vinculadas a pacotes."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.scheduling.exceptions import CompletedPackageSessionRemovalError
from apps.scheduling.models import Appointment, PackageSession, PatientPackage


@transaction.atomic
def cancel_patient_package(*, actor, package: PatientPackage) -> PatientPackage:
    locked = PatientPackage.objects.select_for_update().get(pk=package.pk)
    locked.status = PatientPackage.Status.CANCELLED
    locked.save(update_fields=["status", "updated_at"])
    locked.appointments.select_for_update().filter(
        start_time__gte=timezone.now(),
        status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
    ).update(
        status=Appointment.Status.CANCELLED,
        cancellation_reason="Pacote cancelado.",
    )
    return locked


@transaction.atomic
def remove_package_session(*, actor, package_session: PackageSession) -> PatientPackage:
    item = (
        PackageSession.objects.select_for_update()
        .select_related("package", "appointment")
        .get(pk=package_session.pk)
    )
    if item.status == PackageSession.Status.COMPLETED:
        raise CompletedPackageSessionRemovalError(
            "Sessões realizadas não podem ser removidas."
        )
    if item.appointment:
        item.appointment.status = Appointment.Status.CANCELLED
        item.appointment.cancellation_reason = "Sessão removida do pacote."
        item.appointment.updated_by = actor
        item.appointment.save(
            update_fields=[
                "status",
                "cancellation_reason",
                "updated_by",
                "updated_at",
            ]
        )
    package = item.package
    if item.consumed:
        package.release()
    item.delete()
    return package


__all__ = ["cancel_patient_package", "remove_package_session"]
