from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Payment, Plan
from apps.billing.serializers import (
    ChangePlanSerializer,
    CheckoutCreateSerializer,
    CheckoutPreviewSerializer,
    CreateSubscriptionSerializer,
    PaymentSerializer,
    PlanSerializer,
    SubscriptionSerializer,
)
from apps.billing.services.gateways.asaas import AsaasGateway
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.subscriptions import (
    cancel_subscription,
    change_plan,
    create_subscription_for_user,
    get_current_subscription,
)
from apps.billing.webhooks.asaas import handle_asaas_webhook


def _validation_detail(exc: DjangoValidationError) -> str:
    return exc.messages[0] if getattr(exc, "messages", None) else str(exc)


def _checkout_response_payload(validated_data: dict) -> dict:
    plan = validated_data["plan"]
    return {
        "gateway": "ASAAS",
        "environment": "SANDBOX" if "sandbox" in settings.ASAAS_BASE_URL.lower() else "PRODUCTION",
        "notice": "Os pagamentos serão processados pelo Asaas.",
        "activation_rule": "Nada no frontend ativa plano. A assinatura só vira ACTIVE após webhook do Asaas.",
        "plan": PlanSerializer(plan).data,
        "checkout": {
            "type": validated_data["type"],
            "billingType": validated_data["billingType"],
            "dueDate": validated_data["dueDate"].isoformat(),
            "value": str(validated_data["value"]),
            "description": validated_data["description"],
            "cycle": validated_data["cycle"],
            "installmentCount": validated_data.get("installmentCount", 1),
        },
    }


def _public_payment_payload(gateway_payment: dict) -> dict:
    """Retorna somente dados do gateway necessários para o fluxo do cliente.

    O payload bruto pode conter dados pessoais, informações de cobrança e campos
    adicionados pelo provedor no futuro. Por isso, a resposta pública usa uma
    allowlist explícita em vez de encaminhar o objeto integral ao navegador.
    """

    return {
        "gateway_payment_id": gateway_payment.get("id"),
        "status": gateway_payment.get("status", "PENDING"),
        "invoiceUrl": gateway_payment.get("invoiceUrl") or gateway_payment.get("invoice_url"),
        "bankSlipUrl": gateway_payment.get("bankSlipUrl") or gateway_payment.get("bank_slip_url"),
    }


class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by("price", "name")


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
        serializer = CheckoutPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(_checkout_response_payload(serializer.validated_data), status=status.HTTP_200_OK)


class CheckoutCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        checkout_data = serializer.validated_data
        plan = checkout_data["plan"]
        try:
            if checkout_data["type"] == "SUBSCRIPTION":
                subscription = create_subscription_for_user(request.user, plan, checkout_data)
                payload = _checkout_response_payload(checkout_data)
                payload["subscription"] = SubscriptionSerializer(subscription).data
                payload["status"] = subscription.status
                return Response(payload, status=status.HTTP_201_CREATED)

            gateway_payment = AsaasGateway().create_payment(request.user, checkout_data)
            payload = _checkout_response_payload(checkout_data)
            payload["payment"] = _public_payment_payload(gateway_payment)
            return Response(payload, status=status.HTTP_201_CREATED)
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            subscription = create_subscription_for_user(request.user, serializer.validated_data["plan"])
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            subscription = cancel_subscription(request.user)
        except DjangoValidationError as exc:
            return Response({"detail": _validation_detail(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
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
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user_id=self.request.user.pk).order_by("-due_date", "-created_at")


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
                "event_type": event.event_type,
            },
            status=status.HTTP_200_OK,
        )
