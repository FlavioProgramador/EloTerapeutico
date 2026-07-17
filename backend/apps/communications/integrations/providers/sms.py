from __future__ import annotations

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
            raise RetryableProviderError(
                "A API da Twilio está temporariamente indisponível."
            ) from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais da Twilio inválidas.")
        if response.status_code >= 500:
            raise RetryableProviderError(
                "A API da Twilio está temporariamente indisponível."
            )
        if response.status_code >= 400:
            raise PermanentProviderError(
                "A Twilio rejeitou a configuração informada."
            )
        self._sender()

    def _send_sms(self, destination: str, body: str) -> ProviderResult:
        digits = "".join(
            char for char in destination if char.isdigit() or char == "+"
        )
        if len("".join(char for char in digits if char.isdigit())) < 10:
            raise InvalidRecipient("Telefone inválido para SMS.")
        account_sid, auth_token = self._auth()
        data = {"To": digits, "From": self._sender(), "Body": body[:1600]}
        callback_url = str(
            self._metadata().get("status_callback_url") or ""
        ).strip()
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
            raise RetryableProviderError(
                "A API da Twilio está temporariamente indisponível."
            ) from exc
        if response.status_code in {401, 403}:
            raise ProviderNotConfigured("Credenciais da Twilio inválidas.")
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableProviderError("A Twilio solicitou uma nova tentativa.")
        if response.status_code >= 400:
            raise PermanentProviderError(
                "A Twilio rejeitou a mensagem ou o destinatário."
            )
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
        return self._send_sms(
            target,
            "Teste do canal SMS do Elo Terapêutico.",
        )
