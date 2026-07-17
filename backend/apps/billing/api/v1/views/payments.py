from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.v1.serializers import PaymentSerializer
from apps.billing.selectors.payments import (
    get_payment_summary,
    get_payments_for_user,
)
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.payment_sync import (
    PaymentRefreshUnavailable,
    refresh_gateway_payment,
)

from .common import gateway_error_response


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_payments_for_user(
            user=self.request.user,
            payment_status=self.request.query_params.get("status"),
            order_public_id=self.request.query_params.get("order"),
            ordering=self.request.query_params.get("ordering", "due_date"),
        )


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_payments_for_user(user=self.request.user)


class PaymentRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            payment = refresh_gateway_payment(
                user=request.user,
                payment_id=pk,
            )
        except PaymentRefreshUnavailable:
            return Response(
                {
                    "detail": (
                        "Fatura não encontrada ou indisponível para "
                        "sincronização."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except GatewayError:
            return gateway_error_response("payment_refresh")
        return Response(PaymentSerializer(payment).data)


class PaymentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            get_payment_summary(
                user=request.user,
                order_public_id=request.query_params.get("order"),
            )
        )
