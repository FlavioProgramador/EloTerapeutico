from __future__ import annotations

from urllib.parse import quote

import httpx

from apps.communications.models import Communication

from .base import (
    CommunicationProvider,
    InvalidRecipient,
    PermanentProviderError,
    ProviderNotConfigured,
    ProviderResult,
    RetryableProviderError,
)


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
                "manual_url": self._build_url(
                    target,
                    "Teste do WhatsApp manual do Elo Terapêutico.",
                ),
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
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

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
            raise RetryableProviderError(
                "A API do WhatsApp está temporariamente indisponível."
            ) from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured(
                "Credenciais do WhatsApp inválidas ou sem permissão."
            )
        if response.status_code >= 500:
            raise RetryableProviderError(
                "A API do WhatsApp está temporariamente indisponível."
            )
        if response.status_code >= 400:
            raise PermanentProviderError(
                "A Meta rejeitou a configuração informada."
            )

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
            raise RetryableProviderError(
                "A API do WhatsApp está temporariamente indisponível."
            ) from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured(
                "Credenciais do WhatsApp inválidas ou expiradas."
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError(
                "A API do WhatsApp solicitou uma nova tentativa."
            )
        if response.status_code >= 400:
            raise PermanentProviderError(
                "A Meta rejeitou a mensagem. Verifique template, janela e destinatário."
            )
        payload = response.json()
        messages = payload.get("messages") if isinstance(payload, dict) else None
        external_id = str(messages[0].get("id") if messages else "")
        return ProviderResult(
            success=True,
            provider_message_id=external_id,
            status=Communication.Status.SENT,
        )

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        return self._send_text(recipient.destination or "", communication.body or "")

    def send_test(self, owner, destination: str | None = None) -> ProviderResult:
        self.validate_configuration(owner)
        target = destination or getattr(owner, "phone", "") or ""
        return self._send_text(
            target,
            "Teste do canal WhatsApp Business do Elo Terapêutico.",
        )
