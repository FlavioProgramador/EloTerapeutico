"""Fachada de compatibilidade para modelos financeiros.

Os modelos foram organizados em `model_parts/`, preservando imports públicos
como `from apps.financeiro.models import FinancialTransaction`.
"""

from .model_parts import FinancialTransaction, MonthlySubscription

__all__ = ["FinancialTransaction", "MonthlySubscription"]
