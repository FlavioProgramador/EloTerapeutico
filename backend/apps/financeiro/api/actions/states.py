"""Actions de transição de estado financeiro."""

from rest_framework.decorators import action
from rest_framework.response import Response

from ...serializers import TransactionDetailSerializer
from ...services.cancellations import cancel_transaction
from ...services.reversals import reverse_payment


class TransactionStateActions:
    def _serialize_transaction(self, request, financial_transaction):
        serializer = TransactionDetailSerializer(
            financial_transaction,
            context={"request": request},
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        current = cancel_transaction(financial_transaction=self.get_object())
        return self._serialize_transaction(request, current)

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        current = reverse_payment(financial_transaction=self.get_object())
        return self._serialize_transaction(request, current)
