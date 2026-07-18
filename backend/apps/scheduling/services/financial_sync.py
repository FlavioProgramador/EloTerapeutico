"""Sincronização explícita entre Agenda e Financeiro."""

from apps.agenda.models import Appointment


def create_financial_transaction(*, appointment: Appointment) -> None:
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


def cancel_financial_transaction(*, appointment: Appointment) -> None:
    from apps.financeiro.models import FinancialTransaction

    transaction_item = FinancialTransaction.objects.filter(
        appointment=appointment,
        source=FinancialTransaction.Source.APPOINTMENT,
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
    ).first()
    if transaction_item:
        transaction_item.cancel()
