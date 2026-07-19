"""Compatibilidade com o antigo service de sincronização financeira."""

from apps.scheduling.integrations.finance import (
    cancel_appointment_transaction as cancel_financial_transaction,
)
from apps.scheduling.integrations.finance import (
    create_appointment_transaction as create_financial_transaction,
)

__all__ = ["cancel_financial_transaction", "create_financial_transaction"]
