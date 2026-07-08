import logging
from datetime import timedelta
from typing import Any

import httpx
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .base import GatewayConfigurationError, GatewayError, PaymentGateway

logger = logging.getLogger(__name__)


class AsaasGateway(PaymentGateway):
    gateway_name = "ASAAS"

    def __init__(self) -> None:
        self.api_key = settings.ASAAS_API_KEY
        self.base_url = settings.ASAAS_BASE_URL.rstrip("/")
        self.timeout = 20.0
        if not self.api_key:
            raise GatewayConfigurationError("ASAAS_API_KEY não está configurada.")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": self.api_key,
        }

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, headers=self.headers, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning("asaas_http_error", extra={"status_code": status_code, "path": path})
            if status_code in {400, 401, 403, 404}:
                raise GatewayError("Não foi possível concluir a operação de cobrança. Verifique os dados e tente novamente.")
            raise GatewayError("O gateway de pagamento está temporariamente indisponível.")
        except httpx.HTTPError:
            logger.exception("asaas_request_error", extra={"path": path})
            raise GatewayError("Falha de comunicação com o gateway de pagamento.")

    def create_customer(self, user) -> dict[str, Any]:
        payload = {
            "name": user.full_name,
            "email": user.email,
        }
        if getattr(user, "phone", ""):
            payload["mobilePhone"] = user.phone
        return self._request("POST", "/customers", json=payload)

    def create_subscription(self, user, plan, customer_id: str | None = None) -> dict[str, Any]:
        if not customer_id:
            customer = self.create_customer(user)
            customer_id = customer.get("id")
        if not customer_id:
            raise GatewayError("Gateway não retornou o identificador do cliente.")

        trial_days = max(int(settings.BILLING_TRIAL_DAYS), 0)
        next_due_date = timezone.localdate() + timedelta(days=trial_days)
        payload = {
            "customer": customer_id,
            "billingType": "UNDEFINED",
            "value": float(plan.price),
            "cycle": "MONTHLY" if plan.billing_cycle == plan.BillingCycle.MONTHLY else "YEARLY",
            "description": f"Assinatura Elo Terapêutico - {plan.name}",
            "nextDueDate": next_due_date.isoformat(),
            "externalReference": f"elo-plan-{plan.slug}-user-{user.pk}",
        }
        return self._request("POST", "/subscriptions", json=payload)

    def cancel_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/subscriptions/{gateway_subscription_id}")

    def get_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{gateway_subscription_id}")

    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{gateway_payment_id}")

    def parse_webhook(self, request) -> dict[str, Any]:
        configured_token = settings.ASAAS_WEBHOOK_TOKEN
        received_token = (
            request.headers.get("asaas-access-token")
            or request.headers.get("x-asaas-token")
            or request.headers.get("x-webhook-token")
            or request.headers.get("authorization", "").removeprefix("Bearer ")
        )
        if configured_token and received_token != configured_token:
            raise PermissionDenied("Webhook Asaas inválido.")
        if not configured_token:
            logger.warning("asaas_webhook_token_not_configured")
        return request.data
