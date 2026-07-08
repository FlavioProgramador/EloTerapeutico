"""Composição canônica do ViewSet financeiro."""

from ..selectors.transactions import transactions_accessible_to
from .actions import (
    BillingActions,
    FinancialSummaryActions,
    SubscriptionActions,
    TransactionListActions,
    TransactionPaymentActions,
    TransactionReportActions,
    TransactionStateActions,
)
from .views import TransactionViewSet as LegacyTransactionViewSet


class TransactionViewSet(
    FinancialSummaryActions,
    BillingActions,
    SubscriptionActions,
    TransactionPaymentActions,
    TransactionStateActions,
    TransactionListActions,
    TransactionReportActions,
    LegacyTransactionViewSet,
):
    def get_queryset(self):
        return transactions_accessible_to(self.request.user)
