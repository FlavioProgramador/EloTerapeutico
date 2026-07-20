"""Registros administrativos do domínio financeiro."""

from .financial_transactions import FinancialTransactionAdmin
from .monthly_subscriptions import MonthlySubscriptionAdmin

__all__ = ["FinancialTransactionAdmin", "MonthlySubscriptionAdmin"]
