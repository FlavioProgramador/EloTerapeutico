"""Actions HTTP de pagamentos."""

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.finances.api.v1.serializers import (
    MarkAsPaidSerializer,
    TransactionDetailSerializer,
)
from apps.finances.services import register_payment


class PaymentActionsMixin:
    @action(detail=True, methods=["patch"], url_path="pay")
    def mark_as_paid(self, request, pk=None):
        current = self.get_object()
        serializer = MarkAsPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current = register_payment(
            financial_transaction=current, **serializer.validated_data
        )
        return Response(
            TransactionDetailSerializer(
                current, context={"request": request}
            ).data
        )
