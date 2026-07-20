"""Actions HTTP de cancelamento e estorno."""

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import TransactionDetailSerializer
from apps.finances.services import cancel_transaction, refund_transaction


class TransactionStateActionsMixin:
    def _state_response(self, request, instance):
        return Response(
            TransactionDetailSerializer(
                instance, context={"request": request}
            ).data
        )

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        return self._state_response(
            request, cancel_transaction(financial_transaction=self.get_object())
        )

    @action(detail=True, methods=["post"], url_path="refund")
    def refund(self, request, pk=None):
        return self._state_response(
            request, refund_transaction(financial_transaction=self.get_object())
        )
