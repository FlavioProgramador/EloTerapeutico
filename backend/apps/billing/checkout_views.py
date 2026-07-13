import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.selectors.orders import get_order_with_payments
from apps.billing.serializers import (
    BillingOrderSerializer,
    CheckoutCreateSerializer,
    PaymentSerializer,
    SubscriptionSerializer,
)
from apps.billing.services.checkout import CheckoutBusinessError, create_checkout_order
from apps.billing.services.gateways.base import GatewayError
from apps.billing.services.integration_health import get_billing_integration_health
from apps.billing.views import _checkout_response_payload, _service_checkout_data

logger = logging.getLogger(__name__)


def _plain_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain_details(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_details(item) for item in value]
    return str(value)


def _error_response(*, code: str, message: str, http_status: int, details=None) -> Response:
    return Response(
        {
            # Compatibilidade com consumidores legados do DRF.
            "detail": message,
            "error": {
                "code": code,
                "message": message,
                "details": _plain_details(details or {}),
            },
        },
        status=http_status,
    )


def _django_validation_details(exc: DjangoValidationError) -> dict[str, Any]:
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    return {"non_field_errors": list(exc.messages)}


def _gateway_message(exc: GatewayError) -> str:
    if settings.DEBUG and exc.safe_gateway_message:
        return exc.safe_gateway_message
    return exc.public_message


def _payment_links(payments: list[dict[str, Any]]) -> dict[str, Any]:
    first = payments[0] if payments else {}
    invoice_url = first.get("invoice_url") or None
    payment_url = invoice_url or first.get("bank_slip_url") or None
    pix_copy_paste = first.get("pix_copy_paste") or None
    pix_qr_code = first.get("pix_qr_code") or None
    return {
        "payment_url": payment_url,
        "invoice_url": invoice_url,
        "pix": (
            {"copy_paste": pix_copy_paste, "qr_code": pix_qr_code}
            if pix_copy_paste or pix_qr_code
            else None
        ),
    }


class CheckoutCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutCreateSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return _error_response(
                code="CHECKOUT_VALIDATION_ERROR",
                message="Verifique os dados informados.",
                http_status=status.HTTP_400_BAD_REQUEST,
                details=serializer.errors,
            )

        checkout_data = serializer.validated_data
        try:
            result = create_checkout_order(
                user=request.user,
                plan_price=checkout_data["plan_price"],
                checkout_data=_service_checkout_data(checkout_data),
                idempotency_key=checkout_data["idempotency_key"],
            )
        except CheckoutBusinessError as exc:
            return _error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
                details=exc.details,
            )
        except DjangoValidationError as exc:
            return _error_response(
                code="CHECKOUT_VALIDATION_ERROR",
                message="Verifique os dados informados.",
                http_status=status.HTTP_400_BAD_REQUEST,
                details=_django_validation_details(exc),
            )
        except GatewayError as exc:
            logger.warning(
                "billing_gateway_operation_failed",
                extra={
                    "operation": "checkout_create",
                    "user_id": request.user.pk,
                    "gateway": "ASAAS",
                    "environment": (
                        "SANDBOX" if "sandbox" in settings.ASAAS_BASE_URL.lower() else "PRODUCTION"
                    ),
                    "http_status": exc.http_status,
                    "error_type": exc.__class__.__name__,
                    "safe_error_code": exc.code,
                },
            )
            return _error_response(
                code=exc.code,
                message=_gateway_message(exc),
                http_status=exc.http_status,
                details=exc.details,
            )

        order = get_order_with_payments(order_id=result.order.pk)
        serialized_payments = PaymentSerializer(order.payments.all(), many=True).data
        payload = _checkout_response_payload(checkout_data)
        payload.update(
            {
                "status": order.status,
                "order": BillingOrderSerializer(order).data,
                "subscription": SubscriptionSerializer(result.subscription).data,
                "payments": serialized_payments,
                "idempotent_replay": not result.created,
                **_payment_links(serialized_payments),
            }
        )
        # Mantém o contrato histórico do endpoint: uma repetição idempotente
        # continua sendo uma resposta de criação bem-sucedida, sem nova cobrança.
        return Response(payload, status=status.HTTP_201_CREATED)


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
