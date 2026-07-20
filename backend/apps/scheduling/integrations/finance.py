"""Adapter público de scheduling para o domínio financeiro."""

from __future__ import annotations

from apps.scheduling.models import Appointment, PatientPackage


def create_appointment_transaction(*, appointment: Appointment) -> None:
    from apps.finances.services import create_transaction_for_appointment

    create_transaction_for_appointment(appointment=appointment)


def cancel_appointment_transaction(*, appointment: Appointment) -> None:
    from apps.finances.services import cancel_transaction_for_appointment

    cancel_transaction_for_appointment(appointment=appointment)


def create_package_transaction(*, package: PatientPackage) -> None:
    from apps.finances.services import create_transaction_for_package

    create_transaction_for_package(package=package)


__all__ = [
    "cancel_appointment_transaction",
    "create_appointment_transaction",
    "create_package_transaction",
]
