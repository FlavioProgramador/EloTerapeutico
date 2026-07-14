from __future__ import annotations

from dataclasses import dataclass, field
from email.utils import formataddr
from typing import Any
from urllib.parse import quote

import httpx
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

from .models import Communication, CommunicationChannelConfig, InAppNotification


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

    def __init__(self, config: CommunicationChannelConfig | None = None):
        self.config = config

    def validate_configuration(self, owner=None) -> None:
        raise NotImplementedError

    def send(self, communication, recipient) -> ProviderResult:
        raise NotImplementedError

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        raise ProviderNotConfigured("Este provedor não oferece mensagem de teste.")

    def parse_webhook(self, payload: dict[str, object]) -> dict[str, object]:
        raise ProviderNotConfigured("Webhook não configurado para este provedor.")

    def _metadata(self) -> dict[str, Any]:
        return dict(self.config.metadata) if self.config else {}

    def _credentials(self) -> dict[str, Any]:
        return self.config.get_credentials() if self.config else {}


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

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        InAppNotification.objects.create(
            owner=owner,
            recipient=owner,
            communication=None,
            title="Teste do canal interno",
            message="A central de notificações do Elo Terapêutico está funcionando.",
            notification_type="channel.test",
        )
        return ProviderResult(success=True, status=Communication.Status.DELIVERED)


class EmailProvider(CommunicationProvider):
    channel = Communication.Channel.EMAIL
    name = "django_email"

    def _sender(self, owner) -> str:
        metadata = self._metadata()
        sender_email = str(metadata.get("sender_email") or getattr(settings, "DEFAULT_FROM_EMAIL", "")).strip()
        if not sender_email:
            raise ProviderNotConfigured("Remetente de e-mail não configurado.")
        sender_name = str(metadata.get("sender_name") or getattr(owner, "clinic_name", "") or "Elo Terapêutico").strip()
        return formataddr((sender_name, sender_email))

    def _reply_to(self) -> list[str] | None:
        reply_to = str(self._metadata().get("reply_to") or getattr(settings, "COMMUNICATIONS_REPLY_TO", "")).strip()
        return [reply_to] if reply_to else None

    def _connection(self):
        return get_connection(fail_silently=False)

    def validate_configuration(self, owner=None) -> None:
        self._sender(owner)
        connection = self._connection()
        try:
            connection.open()
        except Exception as exc:
            raise RetryableProviderError("Não foi possível abrir a conexão de e-mail.") from exc
        finally:
            connection.close()

    def _send_message(self, *, owner, destination: str, subject: str, body: str, body_html: str = "") -> ProviderResult:
        if "@" not in destination:
            raise InvalidRecipient("Destinatário de e-mail inválido.")
        self.validate_configuration(owner)
        message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=self._sender(owner),
            to=[destination],
            reply_to=self._reply_to(),
            connection=self._connection(),
        )
        if body_html:
            message.attach_alternative(body_html, "text/html")
        try:
            sent_count = message.send(fail_silently=False)
        except Exception as exc:
            raise RetryableProviderError("Falha temporária no backend de e-mail.") from exc
        if sent_count != 1:
            raise RetryableProviderError("O backend de e-mail não confirmou o envio.")
        return ProviderResult(success=True, status=Communication.Status.SENT)

    def send(self, communication, recipient) -> ProviderResult:
        return self._send_message(
            owner=communication.owner,
            destination=(recipient.destination or "").strip(),
            subject=communication.subject or "Elo Terapêutico",
            body=communication.body or "",
            body_html=communication.body_html or "",
        )

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        target = (destination or getattr(owner, "email", "") or "").strip()
        return self._send_message(
            owner=owner,
            destination=target,
            subject="Teste do canal de e-mail",
            body="A configuração de e-mail do Elo Terapêutico está funcionando.",
        )


class SMTPEmailProvider(EmailProvider):
    name = "smtp"

    def _connection(self):
        metadata = self._metadata()
        credentials = self._credentials()
        return SMTPEmailBackend(
            host=str(metadata.get("host") or ""),
            port=int(metadata.get("port") or 587),
            username=str(credentials.get("username") or ""),
            password=str(credentials.get("password") or ""),
            use_tls=bool(metadata.get("use_tls", True)),
            use_ssl=bool(metadata.get("use_ssl", False)),
            timeout=int(metadata.get("timeout") or 15),
            fail_silently=False,
        )

    def validate_configuration(self, owner=None) -> None:
        metadata = self._metadata()
        credentials = self._credentials()
        required = {
            "host": metadata.get("host"),
            "port": metadata.get("port"),
            "sender_email": metadata.get("sender_email"),
            "username": credentials.get("username"),
            "password": credentials.get("password"),
        }
        if any(value in (None, "") for value in required.values()):
            raise ProviderNotConfigured("Configuração SMTP incompleta.")
        if metadata.get("use_tls") and metadata.get("use_ssl"):
            raise ProviderNotConfigured("TLS e SSL não podem ser ativados simultaneamente.")
        connection = self._connection()
        try:
            opened = connection.open()
            if opened is False:
                raise RetryableProviderError("O servidor SMTP recusou a conexão.")
        except ProviderError:
            raise
        except Exception as exc:
            raise RetryableProviderError("Não foi possível autenticar no servidor SMTP.") from exc
        finally:
            connection.close()


class WhatsAppManualProvider(CommunicationProvider):
    channel = Communication.Channel.WHATSAPP_MANUAL
    name = "whatsapp_manual"

    def validate_configuration(self, owner=None) -> None:
        return None

    def _build_url(self, phone: str, message: str) -> str:
        digits = "".join(char for char in phone if char.isdigit())
        if len(digits) < 10:
            raise InvalidRecipient("Telefone inválido para WhatsApp.")
        return f"https://wa.me/{digits}?text={quote(message)}"

    def send(self, communication, recipient) -> ProviderResult:
        url = self._build_url(recipient.destination or "", communication.body or "")
        return ProviderResult(
            success=True,
            status=Communication.Status.DRAFT,
            metadata={"manual_url": url, "requires_confirmation": True},
        )

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        target = destination or getattr(owner, "phone", "") or ""
        return ProviderResult(
            success=True,
            status=Communication.Status.DRAFT,
            metadata={
                "manual_url": self._build_url(target, "Teste do WhatsApp manual do Elo Terapêutico."),
                "requires_confirmation": True,
            },
        )


class WhatsAppCloudProvider(CommunicationProvider):
    channel = Communication.Channel.WHATSAPP
    name = "meta_cloud"

    def _base_url(self) -> str:
        version = str(self._metadata().get("api_version") or "v23.0").strip()
        return f"https://graph.facebook.com/{version}"

    def _headers(self) -> dict[str, str]:
        access_token = str(self._credentials().get("access_token") or "").strip()
        if not access_token:
            raise ProviderNotConfigured("Token de acesso do WhatsApp não configurado.")
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    def _phone_number_id(self) -> str:
        value = str(self._metadata().get("phone_number_id") or "").strip()
        if not value:
            raise ProviderNotConfigured("Phone Number ID não configurado.")
        return value

    def validate_configuration(self, owner=None) -> None:
        phone_number_id = self._phone_number_id()
        try:
            response = httpx.get(
                f"{self._base_url()}/{phone_number_id}",
                headers=self._headers(),
                params={"fields": "display_phone_number,verified_name"},
                timeout=15,
            )
        except httpx.RequestError as exc:
            raise RetryableProviderError("A API do WhatsApp está temporariamente indisponível.") from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais do WhatsApp inválidas ou sem permissão.")
        if response.status_code >= 500:
            raise RetryableProviderError("A API do WhatsApp está temporariamente indisponível.")
        if response.status_code >= 400:
            raise PermanentProviderError("A Meta rejeitou a configuração informada.")

    def _send_text(self, destination: str, body: str) -> ProviderResult:
        digits = "".join(char for char in destination if char.isdigit())
        if len(digits) < 10:
            raise InvalidRecipient("Telefone inválido para WhatsApp.")
        try:
            response = httpx.post(
                f"{self._base_url()}/{self._phone_number_id()}/messages",
                headers=self._headers(),
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": digits,
                    "type": "text",
                    "text": {"preview_url": False, "body": body[:4096]},
                },
                timeout=20,
            )
        except httpx.RequestError as exc:
            raise RetryableProviderError("A API do WhatsApp está temporariamente indisponível.") from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais do WhatsApp inválidas ou expiradas.")
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError("A API do WhatsApp solicitou uma nova tentativa.")
        if response.status_code >= 400:
            raise PermanentProviderError("A Meta rejeitou a mensagem. Verifique template, janela e destinatário.")
        payload = response.json()
        messages = payload.get("messages") if isinstance(payload, dict) else None
        external_id = str(messages[0].get("id") if messages else "")
        return ProviderResult(success=True, provider_message_id=external_id, status=Communication.Status.SENT)

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        return self._send_text(recipient.destination or "", communication.body or "")

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        self.validate_configuration(owner)
        target = destination or getattr(owner, "phone", "") or ""
        return self._send_text(target, "Teste do canal WhatsApp Business do Elo Terapêutico.")


class TwilioSMSProvider(CommunicationProvider):
    channel = Communication.Channel.SMS
    name = "twilio"

    def _account_sid(self) -> str:
        value = str(self._metadata().get("account_sid") or "").strip()
        if not value:
            raise ProviderNotConfigured("Account SID da Twilio não configurado.")
        return value

    def _auth(self) -> tuple[str, str]:
        account_sid = self._account_sid()
        auth_token = str(self._credentials().get("auth_token") or "").strip()
        if not auth_token:
            raise ProviderNotConfigured("Auth Token da Twilio não configurado.")
        return account_sid, auth_token

    def _sender(self) -> str:
        sender = str(self._metadata().get("sender") or "").strip()
        if not sender:
            raise ProviderNotConfigured("Número remetente de SMS não configurado.")
        return sender

    def validate_configuration(self, owner=None) -> None:
        account_sid, auth_token = self._auth()
        try:
            response = httpx.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json",
                auth=(account_sid, auth_token),
                timeout=15,
            )
        except httpx.RequestError as exc:
            raise RetryableProviderError("A API da Twilio está temporariamente indisponível.") from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais da Twilio inválidas.")
        if response.status_code >= 500:
            raise RetryableProviderError("A API da Twilio está temporariamente indisponível.")
        if response.status_code >= 400:
            raise PermanentProviderError("A Twilio rejeitou a configuração informada.")
        self._sender()

    def _send_sms(self, destination: str, body: str) -> ProviderResult:
        digits = "".join(char for char in destination if char.isdigit() or char == "+")
        if len("".join(char for char in digits if char.isdigit())) < 10:
            raise InvalidRecipient("Telefone inválido para SMS.")
        account_sid, auth_token = self._auth()
        data = {"To": digits, "From": self._sender(), "Body": body[:1600]}
        callback_url = str(self._metadata().get("status_callback_url") or "").strip()
        if callback_url:
            data["StatusCallback"] = callback_url
        try:
            response = httpx.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data=data,
                timeout=20,
            )
        except httpx.RequestError as exc:
            raise RetryableProviderError("A API da Twilio está temporariamente indisponível.") from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais da Twilio inválidas.")
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError("A Twilio solicitou uma nova tentativa.")
        if response.status_code >= 400:
            raise PermanentProviderError("A Twilio rejeitou a mensagem ou o destinatário.")
        payload = response.json()
        return ProviderResult(
            success=True,
            provider_message_id=str(payload.get("sid") or ""),
            status=Communication.Status.SENT,
            metadata={
                "provider_status": str(payload.get("status") or ""),
                "price": payload.get("price"),
                "price_unit": payload.get("price_unit"),
            },
        )

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        return self._send_sms(recipient.destination or "", communication.body or "")

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        self.validate_configuration(owner)
        target = destination or getattr(owner, "phone", "") or ""
        return self._send_sms(target, "Teste do canal SMS do Elo Terapêutico.")


class DisabledExternalProvider(CommunicationProvider):
    def __init__(self, *, channel: str, name: str, config: CommunicationChannelConfig | None = None):
        super().__init__(config=config)
        self.channel = channel
        self.name = name

    def validate_configuration(self, owner=None) -> None:
        raise ProviderNotConfigured("Canal não configurado.")

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        raise AssertionError("unreachable")


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
    Communication.Channel.SMS: DisabledExternalProvider(channel=Communication.Channel.SMS, name="sms"),
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
        return DisabledExternalProvider(channel=channel, name=provider_name or "not_configured", config=config)
    return factory(config=config)
