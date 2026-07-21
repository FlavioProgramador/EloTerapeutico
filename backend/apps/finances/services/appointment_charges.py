"""Geração idempotente de cobranças relacionadas a scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import IntegrityError, transaction

from apps.finances.exceptions import IneligibleAppointmentChargeError
from apps.finances.integrations.scheduling import (
    eligible_appointments_for_charge,
    package_financial_payload,
)
from apps.finances.models import FinancialTransaction
from apps.finances.selectors import transaction_for_appointment
from apps.finances.services.cancellations import cancel_transaction


@dataclass(frozen=True)
class AppointmentChargeResult:
    created: list[int]
    skipped: list[int]

    @property
    def created_count(self) -> int:
        return len(self.created)

    def as_dict(self) -> dict:
        return {
            "created": self.created,
            "skipped": self.skipped,
            "created_count": self.created_count,
        }


@transaction.atomic
def generate_appointment_charges(
    *,
    actor,
    appointment_ids,
    due_date,
    organization=None,
):
    normalized_ids = [int(value) for value in appointment_ids]
    if not normalized_ids or len(normalized_ids) != len(set(normalized_ids)):
        raise IneligibleAppointmentChargeError(
            "Selecione sessões válidas e sem duplicidade."
        )
    appointments = list(
        eligible_appointments_for_charge(
            actor=actor,
            appointment_ids=normalized_ids,
            organization=organization,
            for_update=True,
        )
    )
    if len(appointments) != len(normalized_ids):
        raise IneligibleAppointmentChargeError(
            "Uma ou mais sessões não pertencem à organização ou não são elegíveis."
        )
    created: list[int] = []
    skipped: list[int] = []
    for appointment in appointments:
        if transaction_for_appointment(appointment=appointment):
            skipped.append(appointment.pk)
            continue
        if not appointment.session_value or appointment.session_value <= 0:
            raise IneligibleAppointmentChargeError(
                f"A sessão {appointment.pk} não possui valor configurado."
            )
        try:
            with transaction.atomic():
                charge = FinancialTransaction.objects.create(
                    organization=appointment.organization,
                    therapist=appointment.therapist,
                    patient=appointment.patient,
                    appointment=appointment,
                    transaction_type=FinancialTransaction.TransactionType.INCOME,
                    category=FinancialTransaction.Category.SESSION,
                    source=FinancialTransaction.Source.APPOINTMENT,
                    amount=appointment.session_value,
                    due_date=due_date,
                    description=f"Sessão de {appointment.start_time:%d/%m/%Y}",
                )
        except IntegrityError:
            skipped.append(appointment.pk)
        else:
            created.append(charge.pk)
    return AppointmentChargeResult(created=created, skipped=skipped)


@transaction.atomic
def create_transaction_for_appointment(*, appointment):
    charge, _ = FinancialTransaction.objects.get_or_create(
        organization=appointment.organization,
        appointment=appointment,
        source=FinancialTransaction.Source.APPOINTMENT,
        defaults={
            "therapist": appointment.therapist,
            "patient": appointment.patient,
            "transaction_type": FinancialTransaction.TransactionType.INCOME,
            "category": FinancialTransaction.Category.SESSION,
            "amount": appointment.session_value,
            "payment_method": FinancialTransaction.PaymentMethod.OTHER,
            "payment_status": FinancialTransaction.PaymentStatus.PENDING,
            "due_date": appointment.start_time.date(),
            "description": f"Consulta de {appointment.patient.display_name}",
        },
    )
    return charge


def cancel_transaction_for_appointment(*, appointment):
    charge = transaction_for_appointment(appointment=appointment)
    if charge and charge.can_cancel():
        return cancel_transaction(financial_transaction=charge)
    return charge


@transaction.atomic
def create_transaction_for_package(*, package):
    payload = package_financial_payload(package=package)
    return FinancialTransaction.objects.create(
        **payload,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        category=FinancialTransaction.Category.SUBSCRIPTION,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
    )
