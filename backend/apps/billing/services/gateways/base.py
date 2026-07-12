from abc import ABC, abstractmethod
from typing import Any


class GatewayError(Exception):
    """Falha controlada de gateway com contrato público estável."""

    code = "GATEWAY_ERROR"
    http_status = 502
    public_message = (
        "Não foi possível concluir a operação de cobrança. "
        "Tente novamente mais tarde."
    )

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        safe_gateway_message: str | None = None,
    ) -> None:
        super().__init__(message or self.public_message)
        self.details = details or {}
        self.safe_gateway_message = safe_gateway_message or ""


class GatewayConfigurationError(GatewayError):
    """Configuração ausente ou incompatível do gateway."""

    code = "ASAAS_CONFIGURATION_ERROR"
    http_status = 503
    public_message = "A integração de pagamentos não está configurada."


class GatewayAuthenticationError(GatewayError):
    """Credencial rejeitada pelo gateway."""

    code = "ASAAS_AUTHENTICATION_ERROR"
    http_status = 502
    public_message = "Não foi possível autenticar a integração de pagamentos."


class GatewayValidationError(GatewayError):
    """Dados de cobrança rejeitados antes ou durante a chamada ao gateway."""

    code = "ASAAS_VALIDATION_ERROR"
    http_status = 400
    public_message = "Verifique os dados de cobrança informados."


class GatewayUnavailableError(GatewayError):
    """Timeout, limite de requisições ou indisponibilidade temporária."""

    code = "ASAAS_UNAVAILABLE"
    http_status = 503
    public_message = "Não foi possível conectar ao Asaas. Tente novamente em instantes."


class PaymentGateway(ABC):
    @abstractmethod
    def create_customer(self, user, checkout_data: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_recurring_subscription(
        self,
        user,
        plan_price,
        checkout_data: dict[str, Any] | None = None,
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_single_payment(
        self,
        user,
        checkout_data: dict[str, Any],
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_installment_payment(
        self,
        user,
        checkout_data: dict[str, Any],
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_subscription(
        self,
        user,
        plan,
        checkout_data: dict[str, Any] | None = None,
        *,
        customer_id: str | None = None,
    ) -> dict[str, Any]:
        """Compatibilidade temporária com integrações legadas."""
        raise NotImplementedError

    @abstractmethod
    def create_payment(self, user, checkout_data: dict[str, Any]) -> dict[str, Any]:
        """Compatibilidade temporária com integrações legadas."""
        raise NotImplementedError

    @abstractmethod
    def cancel_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_subscription_payments(self, gateway_subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_installment(self, gateway_installment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def list_installment_payments(self, gateway_installment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook(self, request) -> dict[str, Any]:
        raise NotImplementedError
