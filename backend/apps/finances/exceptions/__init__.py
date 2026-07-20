"""Exceções públicas do domínio financeiro."""

from .domain import (
    FinancesDomainError,
    FinancialOwnershipError,
    IneligibleAppointmentChargeError,
    InvalidPaymentAmountError,
    InvalidPaymentTransitionError,
    InvalidSubscriptionStatusError,
)

__all__ = [
    "FinancesDomainError",
    "FinancialOwnershipError",
    "IneligibleAppointmentChargeError",
    "InvalidPaymentAmountError",
    "InvalidPaymentTransitionError",
    "InvalidSubscriptionStatusError",
]
