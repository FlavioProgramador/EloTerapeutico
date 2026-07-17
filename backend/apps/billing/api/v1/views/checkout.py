from __future__ import annotations

import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.api.v1.serializers import (
    BillingOrderSerializer,
    CheckoutCreateSerializer,
    CheckoutPreviewSerializer,
    PaymentSerializer,
    SubscriptionSerializer,
)
from apps.billing.selectors.orders import get_order_with_payments
from apps.billing.services.checkout import (
    CheckoutBusinessError,
    create_checkout_order,
)
from apps.billing.services.gateways.base import GatewayError

from .common import (
    checkout_response_payload,
    django_validation_details,
    error_response,
    gateway_message,
    payment_links,
    service_checkout_data,
)

logger = logging.getLogger(__name__)


class CheckoutPreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutPreviewSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            checkout_response_payload(serializer.validated_data),
            status=status.HTTP_200_OK,
        )


class CheckoutCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            return error_response(
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
                checkout_data=service_checkout_data(checkout_data),
                idempotency_key=checkout_data["idempotency_key"],
            )
        except CheckoutBusinessError as exc:
            return error_response(
                code=exc.code,
                message=str(exc),
                http_status=exc.http_status,
                details=exc.details,
            )
        except DjangoValidationError as exc:
            return error_response(
                code="CHECKOUT_VALIDATION_ERROR",
                message="Verifique os dados informados.",
                http_status=status.HTTP_400_BAD_REQUEST,
                details=django_validation_details(exc),
            )
        except GatewayError as exc:
            logger.warning(
                "billing_gateway_operation_failed",
                extra={
                    "operation": "checkout_create",
                    "user_id": request.user.pk,
                    "gateway": "ASAAS",
                    "environment": (
                        "SANDBOX"
                        if "sandbox" in settings.ASAAS_BASE_URL.lower()
                        else "PRODUCTION"
                    ),
                    "http_status": exc.http_status,
                    "error_type": exc.__class__.__name__,
                    "safe_error_code": exc.code,
                },
            )
            return error_response(
                code=exc.code,
                message=gateway_message(exc),
                http_status=exc.http_status,
                details=exc.details,
            )

        order = get_order_with_payments(order_id=result.order.pk)
        serialized_payments = PaymentSerializer(
            order.payments.all(),
            many=True,
        ).data
        payload = checkout_response_payload(checkout_data)
        payload.update(
            {
                "status": order.status,
                "order": BillingOrderSerializer(order).data,
                "subscription": SubscriptionSerializer(
                    result.subscription
                ).data,
                "payments": serialized_payments,
                "idempotent_replay": not result.created,
                **payment_links(serialized_payments),
            }
        )
        # Mantém o contrato histórico do endpoint: uma repetição idempotente
        # continua sendo uma resposta de criação bem-sucedida, sem nova cobrança.
        return Response(payload, status=status.HTTP_201_CREATED)
