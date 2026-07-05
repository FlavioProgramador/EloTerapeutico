"""Composição canônica do ViewSet financeiro."""

from ..selectors.transactions import transactions_accessible_to
from .billing_actions import BillingActions
from .summary_actions import FinancialSummaryActions
from .transaction_list_actions import TransactionListActions
from .transaction_payment_actions import TransactionPaymentActions
from .transaction_report_actions import TransactionReportActions
from .transaction_state_actions import TransactionStateActions
from .views import TransactionViewSet as LegacyTransactionViewSet


class TransactionViewSet(
    FinancialSummaryActions,
    BillingActions,
    TransactionPaymentActions,
    TransactionStateActions,
    TransactionListActions,
    TransactionReportActions,
    LegacyTransactionViewSet,
):
    def get_queryset(self):
        return transactions_accessible_to(self.request.user)
