from typing import Any

from django.conf import settings

from apps.billing.infrastructure.payments.asaas.client import AsaasGateway
from apps.billing.selectors.integrations import get_webhook_delivery_stats
from apps.billing.services.gateways.base import GatewayError


def _public_gateway_message(exc: GatewayError) -> str:
    if settings.DEBUG and exc.safe_gateway_message:
        return exc.safe_gateway_message
    return exc.public_message


def get_billing_integration_health() -> dict[str, Any]:
    try:
        gateway_health = AsaasGateway(require_api_key=False).health_check()
        connected = bool(gateway_health["connected"])
        configured = bool(gateway_health["configured"])
        environment = gateway_health["environment"]
        detail = (
            "Conexão com o Asaas validada."
            if connected
            else "A integração de pagamentos não está configurada."
        )
        error_code = None if connected else "ASAAS_CONFIGURATION_ERROR"
    except GatewayError as exc:
        connected = False
        configured = bool(getattr(settings, "ASAAS_API_KEY", ""))
        environment = (
            "SANDBOX"
            if "sandbox" in str(getattr(settings, "ASAAS_BASE_URL", "")).lower()
            else "PRODUCTION"
        )
        detail = _public_gateway_message(exc)
        error_code = exc.code

    return {
        "gateway": "ASAAS",
        "connected": connected,
        "configured": configured,
        "environment": environment,
        "detail": detail,
        "error_code": error_code,
        **get_webhook_delivery_stats(),
    }
