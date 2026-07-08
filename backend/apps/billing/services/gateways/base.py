from abc import ABC, abstractmethod
from typing import Any


class GatewayError(Exception):
    """Erro de domínio para falhas controladas de gateway."""


class GatewayConfigurationError(GatewayError):
    """Configuração ausente ou inválida do gateway."""


class PaymentGateway(ABC):
    @abstractmethod
    def create_customer(self, user) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def create_subscription(self, user, plan, customer_id: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def cancel_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_subscription(self, gateway_subscription_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def get_payment(self, gateway_payment_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook(self, request) -> dict[str, Any]:
        raise NotImplementedError
