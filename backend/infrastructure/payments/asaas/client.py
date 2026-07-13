import logging
import re
import secrets
import time
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

import httpx
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from apps.billing.services.gateways.base import (
    GatewayAuthenticationError,
    GatewayConfigurationError,
    GatewayError,
    GatewayUnavailableError,
    GatewayValidationError,
    PaymentGateway,
)

logger = logging.getLogger(__name__)
MONEY = Decimal("0.01")
_ALLOWED_BASE_URLS = {
    "https://api-sandbox.asaas.com/v3": "SANDBOX",
    "https://api.asaas.com/v3": "PRODUCTION",
}
_ALLOWED_GATEWAY_PATH = re.compile(
    r"^/(?:customers|payments|subscriptions|installments)"
    r"(?:/[A-Za-z0-9_-]+)?(?:/payments)?$"
)


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


class AsaasGateway(PaymentGateway):
    gateway_name = "ASAAS"

    def __init__(self, *, require_api_key: bool = True) -> None:
        self.api_key = str(getattr(settings, "ASAAS_API_KEY", "") or "").strip()
        self.base_url = str(getattr(settings, "ASAAS_BASE_URL", "") or "").rstrip("/")
        self.timeout = httpx.Timeout(20.0, connect=5.0)
        if self.base_url not in _ALLOWED_BASE_URLS:
            raise GatewayConfigurationError(
                "ASAAS_BASE_URL inválida.",
                details={"base_url": "Use a URL oficial do Sandbox ou da Produção."},
            )
        if require_api_key and not self.api_key:
            raise GatewayConfigurationError("ASAAS_API_KEY não está configurada.")

    @property
    def environment(self) -> str:
        return _ALLOWED_BASE_URLS[self.base_url]

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

    @staticmethod
    def _validated_path(path: str) -> str:
        if not isinstance(path, str) or not _ALLOWED_GATEWAY_PATH.fullmatch(path):
            raise GatewayValidationError("Rota de integração inválida.")
        return path

    def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if not self.api_key:
            raise GatewayConfigurationError("ASAAS_API_KEY não está configurada.")
        safe_path = self._validated_path(path)
        operation = f"{method.upper()} {safe_path.split('/')[1]}"
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                    response = client.request(method, safe_path, headers=self.headers, **kwargs)
                    response.raise_for_status()
                    return response.json() if response.content else {}
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                safe_detail = self._response_error_detail(exc.response)
                logger.warning(
                    "asaas_http_error",
                    extra={
                        "gateway": self.gateway_name,
                        "environment": self.environment,
                        "operation": operation,
                        "http_status": status_code,
                        "error_type": "HTTPStatusError",
                    },
                )
                if status_code in {429, 500, 502, 503, 504}:
                    if attempt + 1 < attempts:
                        time.sleep(0.25 * (2**attempt))
                        continue
                    raise GatewayUnavailableError(safe_gateway_message=safe_detail) from exc
                if status_code in {401, 403}:
                    raise GatewayAuthenticationError(safe_gateway_message=safe_detail) from exc
                if status_code in {400, 404, 422}:
                    raise GatewayValidationError(safe_gateway_message=safe_detail) from exc
                raise GatewayError(safe_gateway_message=safe_detail) from exc
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt + 1 < attempts:
                    time.sleep(0.25 * (2**attempt))
                    continue
                logger.warning(
                    "asaas_request_unavailable",
                    extra={
                        "gateway": self.gateway_name,
                        "environment": self.environment,
                        "operation": operation,
                        "error_type": exc.__class__.__name__,
                    },
                )
                raise GatewayUnavailableError() from exc
            except httpx.HTTPError as exc:
                logger.exception(
                    "asaas_request_error",
                    extra={
                        "gateway": self.gateway_name,
                        "environment": self.environment,
                        "operation": operation,
                        "error_type": exc.__class__.__name__,
                    },
                )
                raise GatewayUnavailableError() from exc
        raise GatewayUnavailableError()

    @staticmethod
    def _money(value: Any) -> float:
        try:
            amount = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise GatewayValidationError(details={"value": ["Informe um valor monetário válido."]}) from exc
        if amount <= 0:
            raise GatewayValidationError(details={"value": ["O valor deve ser maior que zero."]})
        return float(amount)

    @staticmethod
    def _normalize_customer_data(user, checkout_data: dict[str, Any]) -> dict[str, str]:
        name = str(
            checkout_data.get("name")
            or getattr(user, "full_name", "")
            or getattr(user, "email", "")
            or ""
        ).strip()
        if not name:
            raise GatewayValidationError(details={"name": ["Informe o nome para cobrança."]})

        email = str(checkout_data.get("email") or getattr(user, "email", "") or "").strip().lower()
        try:
            validate_email(email)
        except ValidationError as exc:
            raise GatewayValidationError(details={"email": ["Informe um e-mail válido."]}) from exc

        payload = {"name": name, "email": email}
        document = _digits(checkout_data.get("cpfCnpj"))
        if document:
            if len(document) not in {11, 14}:
                raise GatewayValidationError(
                    details={"cpfCnpj": ["Informe CPF com 11 dígitos ou CNPJ com 14 dígitos."]}
                )
            payload["cpfCnpj"] = document

        phone = _digits(checkout_data.get("phone") or getattr(user, "phone", ""))
        if phone:
            if len(phone) not in {10, 11}:
                raise GatewayValidationError(details={"phone": ["Informe telefone com DDD."]})
            payload["mobilePhone"] = phone
        return payload

    @staticmethod
    def _normalize_due_date(value: Any) -> str:
        try:
            parsed = value if isinstance(value, date) else date.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise GatewayValidationError(details={"dueDate": ["Informe uma data de vencimento válida."]}) from exc
        if parsed < timezone.localdate():
            raise GatewayValidationError(
                details={"dueDate": ["O vencimento não pode estar no passado."]}
            )
        return parsed.isoformat()

    def create_customer(self, user, checkout_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/customers",
            json=self._normalize_customer_data(user, checkout_data or {}),
        )

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
        billing_type = str(checkout_data.get("billingType") or "PIX").upper()
        if billing_type not in {"PIX", "BOLETO", "CREDIT_CARD", "UNDEFINED"}:
            raise GatewayValidationError(details={"billingType": ["Forma de pagamento inválida."]})
        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayValidationError(
                details={"billingType": ["Cartão exige tokenização segura ou checkout hospedado do Asaas."]}
            )
        payload: dict[str, Any] = {
            "customer": customer_id,
            "billingType": billing_type,
            "dueDate": self._normalize_due_date(checkout_data.get("dueDate") or self._default_due_date()),
            "description": str(checkout_data.get("description") or "Cobrança Elo Terapêutico").strip(),
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
        billing_type = str(checkout_data.get("billingType") or "UNDEFINED").upper()
        if billing_type not in {"PIX", "BOLETO", "CREDIT_CARD", "UNDEFINED"}:
            raise GatewayValidationError(
                details={"billingType": ["Forma de pagamento inválida."]}
            )
        if billing_type == "CREDIT_CARD" and not checkout_data.get("creditCardToken"):
            raise GatewayValidationError(
                details={"billingType": ["Cartão exige tokenização segura ou checkout hospedado do Asaas."]}
            )
        payload = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": self._money(plan_price.total_amount),
            "cycle": "YEARLY" if plan_price.billing_interval == "YEARLY" else "MONTHLY",
            "description": str(
                checkout_data.get("description") or f"Assinatura Elo Terapêutico - {plan_price.name}"
            ).strip(),
            "nextDueDate": self._normalize_due_date(
                checkout_data.get("dueDate")
                or checkout_data.get("nextDueDate")
                or self._default_due_date()
            ),
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
        payload["value"] = self._money(checkout_data.get("value") or checkout_data.get("totalValue"))
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
            raise GatewayValidationError(details={"installmentCount": ["Selecione ao menos duas parcelas."]})
        payload = self._payment_base_payload(user, checkout_data, customer_id=customer_id)
        payload["installmentCount"] = installment_count
        payload["totalValue"] = self._money(
            checkout_data.get("totalValue") or checkout_data.get("value")
        )
        return self._request("POST", "/payments", json=payload)

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
        configured = bool(self.api_key)
        if not configured:
            return {
                "gateway": self.gateway_name,
                "connected": False,
                "configured": False,
                "environment": self.environment,
            }
        self._request("GET", "/customers", params={"limit": 1})
        return {
            "gateway": self.gateway_name,
            "connected": True,
            "configured": True,
            "environment": self.environment,
        }

    def parse_webhook(self, request) -> dict[str, Any]:
        configured_token = str(getattr(settings, "ASAAS_WEBHOOK_TOKEN", "") or "")
        received_token = str(
            request.headers.get("asaas-access-token")
            or request.headers.get("X-Webhook-Token")
            or ""
        )
        if configured_token:
            if not received_token or not secrets.compare_digest(received_token, configured_token):
                raise PermissionDenied("Webhook Asaas inválido.")
        elif not settings.DEBUG:
            raise PermissionDenied("Webhook Asaas não configurado.")
        else:
            logger.warning("asaas_webhook_token_not_configured")
        return request.data
