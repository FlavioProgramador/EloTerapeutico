"""Views públicas da API financeira."""

from .appointment_charges import AppointmentChargeActionsMixin
from .exports import TransactionExportActionsMixin
from .financial_transactions import FinancialTransactionViewSetBase
from .monthly_subscriptions import MonthlySubscriptionActionsMixin
from .payments import PaymentActionsMixin
from .states import TransactionStateActionsMixin
from .summaries import FinancialSummaryActionsMixin
from .unbilled_appointments import UnbilledAppointmentActionsMixin


class FinancialTransactionViewSet(
    FinancialSummaryActionsMixin,
    AppointmentChargeActionsMixin,
    MonthlySubscriptionActionsMixin,
    PaymentActionsMixin,
    TransactionStateActionsMixin,
    UnbilledAppointmentActionsMixin,
    TransactionExportActionsMixin,
    FinancialTransactionViewSetBase,
):
    """Composição pública dos recursos financeiros versionados."""


TransactionViewSet = FinancialTransactionViewSet

__all__ = ["FinancialTransactionViewSet", "TransactionViewSet"]
