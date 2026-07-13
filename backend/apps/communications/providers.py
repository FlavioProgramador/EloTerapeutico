from __future__ import annotations

from dataclasses import dataclass, field
from email.utils import formataddr
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from .models import Communication, InAppNotification


class ProviderError(Exception):
    retryable = False


class ProviderNotConfigured(ProviderError):
    pass


class InvalidRecipient(ProviderError):
    pass


class RetryableProviderError(ProviderError):
    retryable = True


class PermanentProviderError(ProviderError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderResult:
    success: bool
    provider_message_id: str = ""
    status: str = Communication.Status.SENT
    retryable: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


class CommunicationProvider:
    channel: str
    name: str

    def validate_configuration(self, owner=None) -> None:
        raise NotImplementedError

    def send(self, communication, recipient) -> ProviderResult:
        raise NotImplementedError

    def parse_webhook(self, payload: dict[str, object]) -> dict[str, object]:
        raise ProviderNotConfigured("Webhook não configurado para este provedor.")


class InAppProvider(CommunicationProvider):
    channel = Communication.Channel.IN_APP
    name = "in_app"

    def validate_configuration(self, owner=None) -> None:
        return None

    def send(self, communication, recipient) -> ProviderResult:
        InAppNotification.objects.create(
            owner=communication.owner,
            recipient=communication.owner,
            communication=communication,
            title=communication.subject or "Nova notificação",
            message=(communication.body or "")[:500],
            notification_type=communication.category,
            priority=communication.priority,
            internal_url=str(communication.metadata.get("internal_url", ""))[:500],
        )
        return ProviderResult(success=True, status=Communication.Status.DELIVERED)


class EmailProvider(CommunicationProvider):
    channel = Communication.Channel.EMAIL
    name = "django_email"

    def validate_configuration(self, owner=None) -> None:
        if not getattr(settings, "DEFAULT_FROM_EMAIL", ""):
            raise ProviderNotConfigured("Remetente de e-mail não configurado.")

    def send(self, communication, recipient) -> ProviderResult:
        destination = (recipient.destination or "").strip()
        if "@" not in destination:
            raise InvalidRecipient("Destinatário de e-mail inválido.")
        self.validate_configuration(communication.owner)
        clinic_name = communication.owner.clinic_name or "Elo Terapêutico"
        message = EmailMultiAlternatives(
            subject=communication.subject or "Elo Terapêutico",
            body=communication.body or "",
            from_email=formataddr((clinic_name, settings.DEFAULT_FROM_EMAIL)),
            to=[destination],
            reply_to=[settings.COMMUNICATIONS_REPLY_TO] if getattr(settings, "COMMUNICATIONS_REPLY_TO", "") else None,
        )
        if communication.body_html:
            message.attach_alternative(communication.body_html, "text/html")
        try:
            sent_count = message.send(fail_silently=False)
        except Exception as exc:
            raise RetryableProviderError(exc.__class__.__name__) from exc
        if sent_count != 1:
            raise RetryableProviderError("O backend de e-mail não confirmou o envio.")
        return ProviderResult(success=True, status=Communication.Status.SENT)


class WhatsAppManualProvider(CommunicationProvider):
    channel = Communication.Channel.WHATSAPP_MANUAL
    name = "whatsapp_manual"

    def validate_configuration(self, owner=None) -> None:
        return None

    def send(self, communication, recipient) -> ProviderResult:
        phone = "".join(char for char in (recipient.destination or "") if char.isdigit())
        if len(phone) < 10:
            raise InvalidRecipient("Telefone inválido para WhatsApp.")
        url = f"https://wa.me/{phone}?text={quote(communication.body or '')}"
        return ProviderResult(
            success=True,
            status=Communication.Status.DRAFT,
            metadata={"manual_url": url, "requires_confirmation": True},
        )


class DisabledExternalProvider(CommunicationProvider):
    def __init__(self, *, channel: str, name: str):
        self.channel = channel
        self.name = name

    def validate_configuration(self, owner=None) -> None:
        raise ProviderNotConfigured("Canal não configurado.")

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        raise AssertionError("unreachable")


PROVIDERS: dict[str, CommunicationProvider] = {
    Communication.Channel.IN_APP: InAppProvider(),
    Communication.Channel.EMAIL: EmailProvider(),
    Communication.Channel.WHATSAPP_MANUAL: WhatsAppManualProvider(),
    Communication.Channel.WHATSAPP: DisabledExternalProvider(
        channel=Communication.Channel.WHATSAPP,
        name="whatsapp_business",
    ),
    Communication.Channel.SMS: DisabledExternalProvider(channel=Communication.Channel.SMS, name="sms"),
}


def get_provider(channel: str) -> CommunicationProvider:
    try:
        return PROVIDERS[channel]
    except KeyError as exc:
        raise ProviderNotConfigured("Canal não suportado.") from exc
