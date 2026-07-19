"""Integração pública entre scheduling e o módulo financeiro."""

from __future__ import annotations

from apps.scheduling.models import Appointment, PatientPackage


def create_appointment_transaction(*, appointment: Appointment) -> None:
    from apps.financeiro.models import FinancialTransaction

    FinancialTransaction.objects.get_or_create(
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


def cancel_appointment_transaction(*, appointment: Appointment) -> None:
    from apps.financeiro.models import FinancialTransaction

    transaction_item = FinancialTransaction.objects.filter(
        appointment=appointment,
        source=FinancialTransaction.Source.APPOINTMENT,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
    ).first()
    if transaction_item:
        transaction_item.cancel()


def create_package_transaction(*, package: PatientPackage) -> None:
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


__all__ = [
    "cancel_appointment_transaction",
    "create_appointment_transaction",
    "create_package_transaction",
]
