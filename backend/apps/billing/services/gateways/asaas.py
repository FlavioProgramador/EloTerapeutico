import logging
import secrets
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import httpx
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .base import GatewayConfigurationError, GatewayError, PaymentGateway

logger = logging.getLogger(__name__)


class AsaasGateway(PaymentGateway):
    gateway_name = "ASAAS"

    def __init__(self, *, require_api_key: bool = True) -> None:
        self.api_key = settings.ASAAS_API_KEY
        self.base_url = settings.ASAAS_BASE_URL.rstrip("/")
        self.timeout = 20.0
        if require_api_key and not self.api_key:
            raise GatewayConfigurationError("ASAAS_API_KEY não está configurada.")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "EloTerapeutico/1.0 (Django)",
            "access_token": self.api_key,
        }

    @staticmethod
    def _response_error_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return ""
        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first_error = errors[0]
            if isinstance(first_error, dict):
                return str(first_error.get("description") or first_error.get("message") or "")
        return str(payload.get("description") or payload.get("message") or "")

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
                detail = self._response_error_detail(exc.response)
                if detail:
                    raise GatewayError(
                        "Nao foi possivel concluir a operacao de cobranca. "
                        f"Detalhe do Asaas: {detail}"
                    )
                raise GatewayError("Não foi possível concluir a operação de cobrança. Verifique os dados e tente novamente.")
            raise GatewayError("O gateway de pagamento está temporariamente indisponível.")
        except httpx.HTTPError:
            logger.exception("asaas_request_error", extra={"path": path})
            raise GatewayError("Falha de comunicação com o gateway de pagamento.")

    def create_customer(self, user, checkout_data: dict[str, Any] | None = None) -> dict[str, Any]:
        checkout_data = checkout_data or {}
        payload = {
            "name": getattr(user, "full_name", "") or getattr(user, "email", ""),
            "email": user.email,
        }
        if getattr(user, "phone", ""):
            payload["mobilePhone"] = user.phone
        if checkout_data.get("cpfCnpj"):
            payload["cpfCnpj"] = checkout_data["cpfCnpj"]
        return self._request("POST", "/customers", json=payload)

    def _ensure_customer_id(self, user, checkout_data: dict[str, Any] | None = None) -> str:
        checkout_data = checkout_data or {}
        customer_id = checkout_data.get("customer") or checkout_data.get("customer_id")
        if customer_id:
            return str(customer_id)
        customer = self.create_customer(user, checkout_data)
        customer_id = customer.get("id")
        if not customer_id:
            raise GatewayError("Gateway não retornou o identificador do cliente.")
        return str(customer_id)

    def _default_due_date(self) -> str:
        trial_days = max(int(settings.BILLING_TRIAL_DAYS), 0)
        return (timezone.localdate() + timedelta(days=trial_days or 1)).isoformat()

    def create_subscription(
        self,
        user,
        plan,
        checkout_data: dict[str, Any] | None = None,
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        checkout_data = checkout_data or {}
        customer_id = customer_id or self._ensure_customer_id(user, checkout_data)
        billing_type = checkout_data.get("billingType") or "UNDEFINED"
        due_date = checkout_data.get("dueDate") or checkout_data.get("nextDueDate") or self._default_due_date()
        value = checkout_data.get("value") or plan.price
        cycle = checkout_data.get("cycle") or ("MONTHLY" if plan.billing_cycle == plan.BillingCycle.MONTHLY else "YEARLY")
        description = checkout_data.get("description") or f"Assinatura Elo Terapêutico - {plan.name}"

        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayError("Cartão de crédito será habilitado apenas via checkout/tokenização segura.")

        payload = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": float(value),
            "cycle": cycle,
            "description": description,
            "nextDueDate": str(due_date),
            "externalReference": checkout_data.get("externalReference") or f"elo-plan-{plan.slug}-user-{user.pk}",
        }
        if checkout_data.get("creditCardToken"):
            payload["creditCardToken"] = checkout_data["creditCardToken"]
        return self._request("POST", "/subscriptions", json=payload)

    def create_payment(self, user, checkout_data: dict[str, Any]) -> dict[str, Any]:
        customer_id = self._ensure_customer_id(user, checkout_data)
        billing_type = checkout_data.get("billingType") or "PIX"
        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayError("Cartão de crédito será habilitado apenas via checkout/tokenização segura.")

        value = Decimal(str(checkout_data.get("value") or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        installment_count = int(checkout_data.get("installmentCount") or 1)
        payload: dict[str, Any] = {
            "customer": customer_id,
            "billingType": billing_type,
            "dueDate": str(checkout_data.get("dueDate")),
            "description": checkout_data.get("description") or "Cobrança Elo Terapêutico",
            "externalReference": checkout_data.get("externalReference") or f"elo-payment-user-{user.pk}",
        }
        if installment_count > 1:
            installment_value = (value / Decimal(installment_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            payload["installmentCount"] = installment_count
            payload["installmentValue"] = float(installment_value)
        else:
            payload["value"] = float(value)
        if checkout_data.get("creditCardToken"):
            payload["creditCardToken"] = checkout_data["creditCardToken"]
        return self._request("POST", "/payments", json=payload)

    def cancel_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/subscriptions/{gateway_subscription_id}")

    def get_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{gateway_subscription_id}")

    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{gateway_payment_id}")

    def parse_webhook(self, request) -> dict[str, Any]:
        configured_token = str(settings.ASAAS_WEBHOOK_TOKEN or "")
        received_token = str(
            request.headers.get("asaas-access-token")
            or request.headers.get("x-asaas-token")
            or request.headers.get("x-webhook-token")
            or request.headers.get("authorization", "").removeprefix("Bearer ")
            or ""
        )
        if configured_token and not secrets.compare_digest(received_token, configured_token):
            raise PermissionDenied("Webhook Asaas inválido.")
        if not configured_token:
            logger.warning("asaas_webhook_token_not_configured")
        return request.data
