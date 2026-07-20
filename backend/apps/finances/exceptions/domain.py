"""Exceções de domínio do módulo financeiro."""

from django.core.exceptions import ValidationError


class FinancesDomainError(ValidationError):
    """Erro validável de negócio financeiro."""


class InvalidPaymentTransitionError(FinancesDomainError):
    """Transição de pagamento incompatível com o estado atual."""


class InvalidPaymentAmountError(FinancesDomainError):
    """Valor de pagamento inválido."""


class InvalidSubscriptionStatusError(FinancesDomainError):
    """Status de mensalidade inválido."""


class IneligibleAppointmentChargeError(FinancesDomainError):
    """Consulta não elegível para cobrança."""


class FinancialOwnershipError(FinancesDomainError):
    """Relacionamento financeiro não pertence ao profissional correto."""
