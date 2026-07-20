"""Exceções públicas do domínio financeiro."""

from .domain import (
    FinancialOwnershipError,
    FinancesDomainError,
    IneligibleAppointmentChargeError,
    InvalidPaymentAmountError,
    InvalidPaymentTransitionError,
    InvalidSubscriptionStatusError,
)

__all__ = [
    "FinancialOwnershipError",
    "FinancesDomainError",
    "IneligibleAppointmentChargeError",
    "InvalidPaymentAmountError",
    "InvalidPaymentTransitionError",
    "InvalidSubscriptionStatusError",
]
