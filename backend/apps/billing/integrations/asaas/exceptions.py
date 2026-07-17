"""Exceções públicas da integração Asaas.

Os aliases preservam o contrato HTTP existente e concentram o ponto de importação
junto ao provider que produz as falhas.
"""

from apps.billing.services.gateways.base import (
    GatewayAuthenticationError,
    GatewayConfigurationError,
    GatewayError,
    GatewayUnavailableError,
    GatewayValidationError,
)

AsaasError = GatewayError
AsaasConfigurationError = GatewayConfigurationError
AsaasAuthenticationError = GatewayAuthenticationError
AsaasValidationError = GatewayValidationError
AsaasUnavailableError = GatewayUnavailableError

__all__ = [
    "AsaasAuthenticationError",
    "AsaasConfigurationError",
    "AsaasError",
    "AsaasUnavailableError",
    "AsaasValidationError",
]
