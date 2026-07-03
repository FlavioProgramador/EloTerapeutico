"""Composição canônica do ViewSet financeiro."""

from ..selectors.transactions import transactions_accessible_to
from .transaction_list_actions import TransactionListActions
from .transaction_payment_actions import TransactionPaymentActions
from .transaction_report_actions import TransactionReportActions
from .views import TransactionViewSet as LegacyTransactionViewSet


class TransactionViewSet(
    TransactionPaymentActions,
    TransactionListActions,
    TransactionReportActions,
    LegacyTransactionViewSet,
):
    def get_queryset(self):
        return transactions_accessible_to(self.request.user)
