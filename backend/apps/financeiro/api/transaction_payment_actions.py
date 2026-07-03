"""Action HTTP para registro de pagamento."""

from rest_framework.decorators import action
from rest_framework.response import Response

from ..services.payments import mark_as_paid as apply_payment
from .serializers import TransactionDetailSerializer


class TransactionPaymentActions:
    @action(detail=True, methods=["patch"], url_path="pay")
    def mark_as_paid(self, request, pk=None):
        current = self.get_object()
        serializer = self.get_serializer(current, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        current = apply_payment(
            financial_transaction=current,
            payment_method=serializer.validated_data.get(
                "payment_method",
                current.payment_method,
            ),
            paid_at=serializer.validated_data.get("paid_at"),
        )
        output = TransactionDetailSerializer(current, context={"request": request})
        return Response(output.data)
