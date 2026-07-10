from abc import ABC, abstractmethod
from typing import Any


class GatewayError(Exception):
    """Erro de domínio para falhas controladas de gateway."""


class GatewayConfigurationError(GatewayError):
    """Configuração ausente ou inválida do gateway."""


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
