import logging
import secrets
import time
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import httpx
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .base import GatewayConfigurationError, GatewayError, PaymentGateway

logger = logging.getLogger(__name__)
MONEY = Decimal("0.01")


class AsaasGateway(PaymentGateway):
    gateway_name = "ASAAS"

    def __init__(self, *, require_api_key: bool = True) -> None:
        self.api_key = settings.ASAAS_API_KEY
        self.base_url = settings.ASAAS_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(20.0, connect=5.0)
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
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, headers=self.headers, **kwargs)
                    response.raise_for_status()
                    return response.json() if response.content else {}
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                logger.warning(
                    "asaas_http_error",
                    extra={"status_code": status_code, "path": path, "attempt": attempt + 1},
                )
                if status_code in {429, 500, 502, 503, 504} and attempt + 1 < attempts:
                    time.sleep(0.25 * (2**attempt))
                    continue
                if status_code in {400, 401, 403, 404, 422}:
                    detail = self._response_error_detail(exc.response)
                    if detail:
                        raise GatewayError(
                            "Não foi possível concluir a operação de cobrança. "
                            f"Detalhe do Asaas: {detail}"
                        ) from exc
                    raise GatewayError(
                        "Não foi possível concluir a operação de cobrança. Verifique os dados e tente novamente."
                    ) from exc
                raise GatewayError("O gateway de pagamento está temporariamente indisponível.") from exc
            except httpx.HTTPError as exc:
                if attempt + 1 < attempts:
                    time.sleep(0.25 * (2**attempt))
                    continue
                logger.exception("asaas_request_error", extra={"path": path})
                raise GatewayError("Falha de comunicação com o gateway de pagamento.") from exc
        raise GatewayError("Falha de comunicação com o gateway de pagamento.")

    @staticmethod
    def _money(value) -> float:
        return float(Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP))

    def create_customer(self, user, checkout_data: dict[str, Any] | None = None) -> dict[str, Any]:
        checkout_data = checkout_data or {}
        payload = {
            "name": checkout_data.get("name") or getattr(user, "full_name", "") or getattr(user, "email", ""),
            "email": checkout_data.get("email") or user.email,
        }
        phone = checkout_data.get("phone") or getattr(user, "phone", "")
        if phone:
            payload["mobilePhone"] = phone
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
        trial_days = max(int(getattr(settings, "BILLING_TRIAL_DAYS", 0)), 0)
        return (timezone.localdate() + timedelta(days=trial_days or 1)).isoformat()

    def _payment_base_payload(
        self,
        user,
        checkout_data: dict[str, Any],
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        customer_id = customer_id or self._ensure_customer_id(user, checkout_data)
        billing_type = checkout_data.get("billingType") or "PIX"
        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayError("Cartão de crédito exige tokenização segura ou checkout hospedado.")
        payload: dict[str, Any] = {
            "customer": customer_id,
            "billingType": billing_type,
            "dueDate": str(checkout_data.get("dueDate") or self._default_due_date()),
            "description": checkout_data.get("description") or "Cobrança Elo Terapêutico",
            "externalReference": checkout_data.get("externalReference"),
        }
        if checkout_data.get("creditCardToken"):
            payload["creditCardToken"] = checkout_data["creditCardToken"]
        return payload

    def create_recurring_subscription(
        self,
        user,
        plan_price,
        checkout_data: dict[str, Any] | None = None,
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        checkout_data = checkout_data or {}
        customer_id = customer_id or self._ensure_customer_id(user, checkout_data)
        billing_type = checkout_data.get("billingType") or "UNDEFINED"
        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayError("Cartão de crédito exige tokenização segura ou checkout hospedado.")
        payload = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": self._money(plan_price.total_amount),
            "cycle": "YEARLY" if plan_price.billing_interval == "YEARLY" else "MONTHLY",
            "description": checkout_data.get("description") or f"Assinatura Elo Terapêutico - {plan_price.name}",
            "nextDueDate": str(checkout_data.get("dueDate") or checkout_data.get("nextDueDate") or self._default_due_date()),
            "externalReference": checkout_data.get("externalReference"),
        }
        if checkout_data.get("creditCardToken"):
            payload["creditCardToken"] = checkout_data["creditCardToken"]
        return self._request("POST", "/subscriptions", json=payload)

    def create_single_payment(
        self,
        user,
        checkout_data: dict[str, Any],
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        payload = self._payment_base_payload(user, checkout_data, customer_id=customer_id)
        payload["value"] = self._money(checkout_data.get("value") or checkout_data.get("totalValue") or 0)
        return self._request("POST", "/payments", json=payload)

    def create_installment_payment(
        self,
        user,
        checkout_data: dict[str, Any],
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        installment_count = int(checkout_data.get("installmentCount") or 0)
        if installment_count < 2:
            raise GatewayError("Parcelamentos exigem no mínimo duas parcelas.")
        payload = self._payment_base_payload(user, checkout_data, customer_id=customer_id)
        payload["installmentCount"] = installment_count
        payload["totalValue"] = self._money(checkout_data.get("totalValue") or checkout_data.get("value") or 0)
        return self._request("POST", "/payments", json=payload)

    # Compatibilidade temporária com chamadas antigas.
    def create_subscription(
        self,
        user,
        plan,
        checkout_data: dict[str, Any] | None = None,
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        class LegacyPrice:
            name = plan.name
            total_amount = plan.price
            billing_interval = plan.billing_cycle

        return self.create_recurring_subscription(
            user,
            LegacyPrice(),
            checkout_data,
            customer_id=customer_id,
        )

    def create_payment(self, user, checkout_data: dict[str, Any]) -> dict[str, Any]:
        if int(checkout_data.get("installmentCount") or 1) > 1:
            return self.create_installment_payment(user, checkout_data)
        return self.create_single_payment(user, checkout_data)

    def cancel_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/subscriptions/{gateway_subscription_id}")

    def get_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{gateway_subscription_id}")

    def list_subscription_payments(self, gateway_subscription_id: str) -> dict[str, Any]:
        return self._request("GET", f"/subscriptions/{gateway_subscription_id}/payments")

    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/payments/{gateway_payment_id}")

    def get_installment(self, gateway_installment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/installments/{gateway_installment_id}")

    def list_installment_payments(self, gateway_installment_id: str) -> dict[str, Any]:
        return self._request("GET", f"/installments/{gateway_installment_id}/payments")

    def health_check(self) -> dict[str, Any]:
        return self._request("GET", "/customers", params={"limit": 1})

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
