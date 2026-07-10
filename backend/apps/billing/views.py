import logging
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Sum
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice, WebhookEvent
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
from apps.billing.services.gateways.asaas import AsaasGateway
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.orders import create_billing_order, upsert_gateway_payment
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


def _validation_detail(exc: DjangoValidationError) -> str:
    return exc.messages[0] if getattr(exc, "messages", None) else str(exc)


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
    blocked = {"plan", "plan_price", "preview", "idempotency_key", "plan_id", "plan_slug", "plan_price_id", "plan_price_slug"}
    return {key: value for key, value in validated_data.items() if key not in blocked}


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).prefetch_related("prices").order_by("name")


class PlanPriceListView(generics.ListAPIView):
    serializer_class = PlanPriceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = PlanPrice.objects.select_related("plan").filter(is_active=True, plan__is_active=True)
        if plan_slug := self.request.query_params.get("plan"):
            queryset = queryset.filter(plan__slug=plan_slug)
        if interval := self.request.query_params.get("billing_interval"):
            queryset = queryset.filter(billing_interval=interval)
        if billing_model := self.request.query_params.get("billing_model"):
            queryset = queryset.filter(billing_model=billing_model)
        return queryset.order_by("plan__name", "billing_interval", "total_amount")


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
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError:
            return _gateway_error_response("checkout_create")

        order = BillingOrder.objects.select_related("plan", "plan_price").prefetch_related("payments").get(pk=order.pk)
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
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError:
            return _gateway_error_response("subscription_create")
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = cancel_subscription(request.user)
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError:
            return _gateway_error_response("subscription_cancel")
        return Response(SubscriptionSerializer(subscription).data)


class ScheduleCancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = schedule_subscription_cancellation(request.user)
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(subscription).data)


class ResumeSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = resume_subscription_cancellation(request.user)
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(subscription).data)


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = change_plan(request.user, serializer.validated_data["plan"])
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
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
        return (
            BillingOrder.objects.filter(user_id=self.request.user.pk)
            .select_related("plan", "plan_price")
            .prefetch_related("payments")
            .order_by("-created_at")
        )


class BillingOrderDetailView(generics.RetrieveAPIView):
    serializer_class = BillingOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def get_queryset(self):
        return (
            BillingOrder.objects.filter(user_id=self.request.user.pk)
            .select_related("plan", "plan_price")
            .prefetch_related("payments")
        )


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.filter(user_id=self.request.user.pk).select_related("billing_order")
        if payment_status := self.request.query_params.get("status"):
            queryset = queryset.filter(status=payment_status)
        if order_public_id := self.request.query_params.get("order"):
            queryset = queryset.filter(billing_order__public_id=order_public_id)
        ordering = self.request.query_params.get("ordering", "due_date")
        allowed = {"due_date", "-due_date", "created_at", "-created_at", "status", "-status"}
        return queryset.order_by(ordering if ordering in allowed else "due_date", "installment_number")


class PaymentDetailView(generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user_id=self.request.user.pk).select_related("billing_order")


class PaymentRefreshView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payment = Payment.objects.select_related("billing_order", "subscription").filter(
            pk=pk,
            user_id=request.user.pk,
        ).first()
        if not payment or not payment.billing_order or not payment.gateway_payment_id:
            return Response({"detail": "Fatura não encontrada ou indisponível para sincronização."}, status=404)
        try:
            payload = AsaasGateway().get_payment(payment.gateway_payment_id)
            payment = upsert_gateway_payment(
                order=payment.billing_order,
                payload=payload,
                subscription=payment.subscription,
                installment_count=payment.installment_count,
            )
        except GatewayError:
            return _gateway_error_response("payment_refresh")
        return Response(PaymentSerializer(payment).data)


class PaymentSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Payment.objects.filter(user_id=request.user.pk)
        if order_public_id := request.query_params.get("order"):
            queryset = queryset.filter(billing_order__public_id=order_public_id)
        paid = queryset.filter(status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED])
        pending = queryset.filter(status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE])
        total = queryset.aggregate(value=Sum("amount"))["value"] or Decimal("0.00")
        paid_total = paid.aggregate(value=Sum("amount"))["value"] or Decimal("0.00")
        next_payment = pending.order_by("due_date").first()
        return Response(
            {
                "total_amount": str(total),
                "paid_amount": str(paid_total),
                "paid_installments": paid.count(),
                "total_installments": queryset.count(),
                "next_due_date": next_payment.due_date if next_payment else None,
                "overdue_installments": queryset.filter(status=Payment.Status.OVERDUE).count(),
            }
        )


class BillingIntegrationHealthView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            AsaasGateway().health_check()
            connected = True
            detail = "Conexão com o Asaas validada."
        except GatewayError:
            connected = False
            detail = "Não foi possível validar a conexão com o Asaas."
        last_event = WebhookEvent.objects.order_by("-received_at").first()
        return Response(
            {
                "gateway": "ASAAS",
                "connected": connected,
                "environment": "SANDBOX" if "sandbox" in settings.ASAAS_BASE_URL.lower() else "PRODUCTION",
                "detail": detail,
                "last_webhook_at": last_event.received_at if last_event else None,
                "pending_events": WebhookEvent.objects.filter(status__in=[WebhookEvent.Status.RECEIVED, WebhookEvent.Status.RETRY]).count(),
                "failed_events": WebhookEvent.objects.filter(status=WebhookEvent.Status.FAILED).count(),
            },
            status=status.HTTP_200_OK if connected else status.HTTP_503_SERVICE_UNAVAILABLE,
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
