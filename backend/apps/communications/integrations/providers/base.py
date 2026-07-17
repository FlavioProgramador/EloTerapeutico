from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.communications.models import Communication, CommunicationChannelConfig


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


class DisabledExternalProvider(CommunicationProvider):
    def __init__(
        self,
        *,
        channel: str,
        name: str,
        config: CommunicationChannelConfig | None = None,
    ):
        super().__init__(config=config)
        self.channel = channel
        self.name = name

    def validate_configuration(self, owner=None) -> None:
        raise ProviderNotConfigured("Canal não configurado.")

    def send(self, communication, recipient) -> ProviderResult:
        self.validate_configuration(communication.owner)
        raise AssertionError("unreachable")
