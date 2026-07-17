from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response

from apps.billing.api.v1.serializers import PlanPriceSerializer, PlanSerializer
from apps.billing.services.gateways.base import GatewayError

logger = logging.getLogger(__name__)


def validation_error_response() -> Response:
    return Response(
        {"detail": "Não foi possível concluir a operação com os dados informados."},
        status=status.HTTP_400_BAD_REQUEST,
    )


def gateway_error_response(operation: str) -> Response:
    logger.warning(
        "billing_gateway_operation_failed",
        extra={"operation": operation},
    )
    return Response(
        {
            "detail": (
                "Não foi possível concluir a operação de cobrança. "
                "Tente novamente mais tarde."
            )
        },
        status=status.HTTP_502_BAD_GATEWAY,
    )


def public_checkout_data(validated_data: dict) -> dict:
    preview = validated_data["preview"]
    return {
        "billingType": validated_data["billingType"],
        "dueDate": validated_data["dueDate"].isoformat(),
        "description": validated_data["description"],
        "billingModel": preview["billing_model"],
        "billingInterval": preview["billing_interval"],
        "totalAmount": str(preview["total_amount"]),
        "installmentCount": preview["installment_count"],
        "installmentAmountEstimate": str(
            preview["installment_amount_estimate"]
        ),
        "discountPercentage": str(preview["discount_percentage"]),
    }


def checkout_response_payload(validated_data: dict) -> dict:
    return {
        "gateway": "ASAAS",
        "environment": (
            "SANDBOX"
            if "sandbox" in settings.ASAAS_BASE_URL.lower()
            else "PRODUCTION"
        ),
        "notice": "Os pagamentos são processados pelo Asaas.",
        "activation_rule": (
            "O frontend não ativa o plano. "
            "O acesso depende da confirmação do gateway."
        ),
        "plan": PlanSerializer(validated_data["plan"]).data,
        "plan_price": PlanPriceSerializer(validated_data["plan_price"]).data,
        "checkout": public_checkout_data(validated_data),
    }


def service_checkout_data(validated_data: dict) -> dict:
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
    return {
        key: value
        for key, value in validated_data.items()
        if key not in blocked
    }


def plain_details(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): plain_details(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain_details(item) for item in value]
    return str(value)


def error_response(
    *,
    code: str,
    message: str,
    http_status: int,
    details=None,
) -> Response:
    return Response(
        {
            "detail": message,
            "error": {
                "code": code,
                "message": message,
                "details": plain_details(details or {}),
            },
        },
        status=http_status,
    )


def django_validation_details(
    exc: DjangoValidationError,
) -> dict[str, Any]:
    if hasattr(exc, "message_dict"):
        return exc.message_dict
    return {"non_field_errors": list(exc.messages)}


def gateway_message(exc: GatewayError) -> str:
    if settings.DEBUG and exc.safe_gateway_message:
        return exc.safe_gateway_message
    return exc.public_message


def payment_links(payments: list[dict[str, Any]]) -> dict[str, Any]:
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
