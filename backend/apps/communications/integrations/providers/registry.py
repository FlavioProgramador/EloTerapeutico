from __future__ import annotations

from apps.communications.models import Communication, CommunicationChannelConfig

from .base import (
    CommunicationProvider,
    DisabledExternalProvider,
    ProviderNotConfigured,
)
from .email import EmailProvider, SMTPEmailProvider
from .in_app import InAppProvider
from .sms import TwilioSMSProvider
from .whatsapp import WhatsAppCloudProvider, WhatsAppManualProvider

DEFAULT_PROVIDER_NAMES: dict[str, str] = {
    Communication.Channel.IN_APP: "in_app",
    Communication.Channel.EMAIL: "django_email",
    Communication.Channel.WHATSAPP_MANUAL: "whatsapp_manual",
    Communication.Channel.WHATSAPP: "whatsapp_business",
    Communication.Channel.SMS: "sms",
}

PROVIDERS: dict[str, CommunicationProvider] = {
    Communication.Channel.IN_APP: InAppProvider(),
    Communication.Channel.EMAIL: EmailProvider(),
    Communication.Channel.WHATSAPP_MANUAL: WhatsAppManualProvider(),
    Communication.Channel.WHATSAPP: DisabledExternalProvider(
        channel=Communication.Channel.WHATSAPP,
        name="whatsapp_business",
    ),
    Communication.Channel.SMS: DisabledExternalProvider(
        channel=Communication.Channel.SMS,
        name="sms",
    ),
}

PROVIDER_FACTORIES = {
    (Communication.Channel.IN_APP, "in_app"): InAppProvider,
    (Communication.Channel.EMAIL, "django_email"): EmailProvider,
    (Communication.Channel.EMAIL, "smtp"): SMTPEmailProvider,
    (Communication.Channel.WHATSAPP_MANUAL, "whatsapp_manual"): WhatsAppManualProvider,
    (Communication.Channel.WHATSAPP, "meta_cloud"): WhatsAppCloudProvider,
    (Communication.Channel.SMS, "twilio"): TwilioSMSProvider,
}


def get_provider(
    channel: str,
    *,
    config: CommunicationChannelConfig | None = None,
) -> CommunicationProvider:
    try:
        fallback = PROVIDERS[channel]
    except KeyError as exc:
        raise ProviderNotConfigured("Canal não suportado.") from exc

    # Mantém a possibilidade de injetar providers nos testes sem chamadas externas.
    if fallback.name != DEFAULT_PROVIDER_NAMES.get(channel):
        return fallback
    if config is None:
        return fallback

    provider_name = config.provider or DEFAULT_PROVIDER_NAMES.get(channel, "")
    factory = PROVIDER_FACTORIES.get((channel, provider_name))
    if factory is None:
        return DisabledExternalProvider(
            channel=channel,
            name=provider_name or "not_configured",
            config=config,
        )
    return factory(config=config)
