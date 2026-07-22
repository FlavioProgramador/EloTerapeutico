class TelemedicineProviderError(Exception):
    """Falha controlada ao conversar com o provedor de mídia."""


class TelemedicineProviderConfigurationError(TelemedicineProviderError):
    """Credenciais ou endpoint do provedor estão incompletos."""


class TelemedicineWebhookVerificationError(TelemedicineProviderError):
    """Webhook inválido ou sem assinatura verificável."""
