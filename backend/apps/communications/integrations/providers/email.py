from __future__ import annotations

from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

from apps.communications.models import Communication

from .base import (
    CommunicationProvider,
    InvalidRecipient,
    ProviderError,
    ProviderNotConfigured,
    ProviderResult,
    RetryableProviderError,
)


class EmailProvider(CommunicationProvider):
    channel = Communication.Channel.EMAIL
    name = "django_email"

    def _sender(self, owner) -> str:
        metadata = self._metadata()
        sender_email = str(
            metadata.get("sender_email") or getattr(settings, "DEFAULT_FROM_EMAIL", "")
        ).strip()
        if not sender_email:
            raise ProviderNotConfigured("Remetente de e-mail não configurado.")
        sender_name = str(
            metadata.get("sender_name")
            or getattr(owner, "clinic_name", "")
            or "Elo Terapêutico"
        ).strip()
        return formataddr((sender_name, sender_email))

    def _reply_to(self) -> list[str] | None:
        reply_to = str(
            self._metadata().get("reply_to")
            or getattr(settings, "COMMUNICATIONS_REPLY_TO", "")
        ).strip()
        return [reply_to] if reply_to else None

    def _connection(self):
        return get_connection(fail_silently=False)

    def validate_configuration(self, owner=None) -> None:
        self._sender(owner)
        connection = self._connection()
        try:
            connection.open()
        except Exception as exc:
            raise RetryableProviderError(
                "Não foi possível abrir a conexão de e-mail."
            ) from exc
        finally:
            connection.close()

    def _send_message(
        self,
        *,
        owner,
        destination: str,
        subject: str,
        body: str,
        body_html: str = "",
    ) -> ProviderResult:
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
            raise ProviderNotConfigured(
                "TLS e SSL não podem ser ativados simultaneamente."
            )
        connection = self._connection()
        try:
            opened = connection.open()
            if opened is False:
                raise RetryableProviderError("O servidor SMTP recusou a conexão.")
        except ProviderError:
            raise
        except Exception as exc:
            raise RetryableProviderError(
                "Não foi possível autenticar no servidor SMTP."
            ) from exc
        finally:
            connection.close()
