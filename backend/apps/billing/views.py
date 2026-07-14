import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.selectors.catalog import get_active_plan_prices, get_active_plans
from apps.billing.selectors.orders import get_order_with_payments, get_orders_for_user
from apps.billing.selectors.payments import get_payment_summary, get_payments_for_user
from apps.billing.serializers import (
    BillingOrderSerializer,
    ChangePlanSerializer,
    CheckoutCreateSerializer,
    CheckoutPreviewSerializer,
    CreateSubscriptionSerializer,
    PaymentSerializer,
    PlanPriceSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.integration_health import get_billing_integration_health
from apps.billing.services.orders import create_billing_order
from apps.billing.services.payment_sync import (
    PaymentRefreshUnavailable,
    refresh_gateway_payment,
)
from apps.billing.services.subscriptions import (
    cancel_subscription,
    change_plan,
    create_subscription_for_user,
    get_current_subscription,
    resume_subscription_cancellation,
    schedule_subscription_cancellation,
)
from apps.billing.webhooks.asaas import handle_asaas_webhook

logger = logging.getLogger(__name__)


def _validation_error_response() -> Response:
    return Response(
        {"detail": "Não foi possível concluir a operação com os dados informados."},
        status=status.HTTP_400_BAD_REQUEST,
    )


def _gateway_error_response(operation: str) -> Response:
    logger.warning("billing_gateway_operation_failed", extra={"operation": operation})
    return Response(
        {"detail": "Não foi possível concluir a operação de cobrança. Tente novamente mais tarde."},
        status=status.HTTP_502_BAD_GATEWAY,
    )


def _public_checkout_data(validated_data: dict) -> dict:
    preview = validated_data["preview"]
    return {
        "billingType": validated_data["billingType"],
        "dueDate": validated_data["dueDate"].isoformat(),
        "description": validated_data["description"],
        "billingModel": preview["billing_model"],
        "billingInterval": preview["billing_interval"],
        "totalAmount": str(preview["total_amount"]),
        "installmentCount": preview["installment_count"],
        "installmentAmountEstimate": str(preview["installment_amount_estimate"]),
        "discountPercentage": str(preview["discount_percentage"]),
    }


def _checkout_response_payload(validated_data: dict) -> dict:
    return {
        "gateway": "ASAAS",
        "environment": "SANDBOX" if "sandbox" in settings.ASAAS_BASE_URL.lower() else "PRODUCTION",
        "notice": "Os pagamentos são processados pelo Asaas.",
        "activation_rule": "O frontend não ativa o plano. O acesso depende da confirmação do gateway.",
        "plan": PlanSerializer(validated_data["plan"]).data,
        "plan_price": PlanPriceSerializer(validated_data["plan_price"]).data,
        "checkout": _public_checkout_data(validated_data),
    }


def _service_checkout_data(validated_data: dict) -> dict:
    blocked = {
        "plan",
        "plan_price",
        "preview",
        "idempotency_key",
        "plan_id",
        "plan_slug",
        "plan_price_id",
        "plan_price_slug",
    }
    return {key: value for key, value in validated_data.items() if key not in blocked}


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_active_plans()


class PlanPriceListView(generics.ListAPIView):
    serializer_class = PlanPriceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_active_plan_prices(
            plan_slug=self.request.query_params.get("plan"),
            billing_interval=self.request.query_params.get("billing_interval"),
            billing_model=self.request.query_params.get("billing_model"),
        )


class CurrentSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = get_current_subscription(request.user)
        if not subscription:
            return Response({"subscription": None})
        return Response({"subscription": SubscriptionSerializer(subscription).data})


class CheckoutPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutPreviewSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(_checkout_response_payload(serializer.validated_data), status=status.HTTP_200_OK)


class CheckoutCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        checkout_data = serializer.validated_data
        try:
            order, subscription = create_billing_order(
                user=request.user,
                plan_price=checkout_data["plan_price"],
                checkout_data=_service_checkout_data(checkout_data),
                idempotency_key=checkout_data["idempotency_key"],
            )
        except DjangoValidationError:
            return _validation_error_response()
        except GatewayError:
            return _gateway_error_response("checkout_create")

        order = get_order_with_payments(order_id=order.pk)
        payload = _checkout_response_payload(checkout_data)
        payload["order"] = BillingOrderSerializer(order).data
        payload["subscription"] = SubscriptionSerializer(subscription).data
        payload["payments"] = PaymentSerializer(order.payments.all(), many=True).data
        payload["status"] = subscription.status
        return Response(payload, status=status.HTTP_201_CREATED)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = create_subscription_for_user(request.user, serializer.validated_data["plan"])
        except DjangoValidationError:
            return _validation_error_response()
        except GatewayError:
            return _gateway_error_response("subscription_create")
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = cancel_subscription(request.user)
        except DjangoValidationError:
            return _validation_error_response()
        except GatewayError:
            return _gateway_error_response("subscription_cancel")
        return Response(SubscriptionSerializer(subscription).data)


class ScheduleCancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = schedule_subscription_cancellation(request.user)
        except DjangoValidationError:
            return _validation_error_response()
        return Response(SubscriptionSerializer(subscription).data)


class ResumeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = resume_subscription_cancellation(request.user)
        except DjangoValidationError:
            return _validation_error_response()
        return Response(SubscriptionSerializer(subscription).data)


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = change_plan(request.user, serializer.validated_data["plan"])
        except DjangoValidationError:
            return _validation_error_response()
        return Response(
            {
                "subscription": SubscriptionSerializer(subscription).data,
                "detail": "Troca registrada. Conclua o checkout do novo preço para efetivar a alteração.",
            },
            status=status.HTTP_202_ACCEPTED,
        )


class BillingOrderListView(generics.ListAPIView):
    serializer_class = BillingOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_orders_for_user(user=self.request.user)


class BillingOrderDetailView(generics.RetrieveAPIView):
    serializer_class = BillingOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def get_queryset(self):
        return get_orders_for_user(user=self.request.user)


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
            payment = refresh_gateway_payment(user=request.user, payment_id=pk)
        except PaymentRefreshUnavailable:
            return Response(
                {"detail": "Fatura não encontrada ou indisponível para sincronização."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except GatewayError:
            return _gateway_error_response("payment_refresh")
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


class BillingIntegrationHealthView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        payload = get_billing_integration_health()
        return Response(
            payload,
            status=(
                status.HTTP_200_OK
                if payload["connected"]
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )


class AsaasWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            event = handle_asaas_webhook(request)
        except PermissionDenied:
            return Response({"detail": "Webhook inválido."}, status=status.HTTP_403_FORBIDDEN)
        return Response(
            {
                "received": True,
                "processed": event.processed,
                "status": event.status,
                "event_type": event.event_type,
            },
            status=status.HTTP_200_OK,
        )
