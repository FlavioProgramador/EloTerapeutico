"""Base do ViewSet financeiro.

As ações HTTP ficam em mixins específicos importados por `transaction_viewset.py`.
Este módulo mantém apenas configuração comum do DRF.
"""

from rest_framework import viewsets

from core.audit import AuditLogMixin

from ..filters import FinancialTransactionFilter
from ..permissions import FinancialPermission
from ..serializers import (
    MarkAsPaidSerializer,
    TransactionCreateUpdateSerializer,
    TransactionDetailSerializer,
    TransactionListSerializer,
)


class TransactionViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """Base para gestão de transações financeiras."""

    permission_classes = [FinancialPermission]
    filterset_class = FinancialTransactionFilter
    ordering_fields = ["created_at", "due_date", "amount", "payment_status"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TransactionCreateUpdateSerializer
        if self.action == "list":
            return TransactionListSerializer
        if self.action == "mark_as_paid":
            return MarkAsPaidSerializer
        return TransactionDetailSerializer
