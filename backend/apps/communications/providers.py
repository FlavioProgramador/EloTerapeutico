"""Compatibilidade para imports antigos de provedores.

Novos imports devem utilizar ``apps.communications.integrations.providers``.
"""

from .integrations.providers import (
    DEFAULT_PROVIDER_NAMES,
    PROVIDER_FACTORIES,
    PROVIDERS,
    CommunicationProvider,
    DisabledExternalProvider,
    EmailProvider,
    InAppProvider,
    InvalidRecipient,
    PermanentProviderError,
    ProviderError,
    ProviderNotConfigured,
    ProviderResult,
    RetryableProviderError,
    SMTPEmailProvider,
    TwilioSMSProvider,
    WhatsAppCloudProvider,
    WhatsAppManualProvider,
    get_provider,
)

__all__ = [
    "CommunicationProvider",
    "DEFAULT_PROVIDER_NAMES",
    "DisabledExternalProvider",
    "EmailProvider",
    "InAppProvider",
    "InvalidRecipient",
    "PROVIDER_FACTORIES",
    "PROVIDERS",
    "PermanentProviderError",
    "ProviderError",
    "ProviderNotConfigured",
    "ProviderResult",
    "RetryableProviderError",
    "SMTPEmailProvider",
    "TwilioSMSProvider",
    "WhatsAppCloudProvider",
    "WhatsAppManualProvider",
    "get_provider",
]
