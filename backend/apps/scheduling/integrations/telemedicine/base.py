from __future__ import annotations

from typing import Protocol

from .types import ParticipantCredentials, ProviderRoom, ProviderWebhookEvent


class TelemedicineProvider(Protocol):
    @property
    def configured(self) -> bool: ...

    def create_room(
        self,
        *,
        room_name: str,
        max_participants: int,
        empty_timeout_seconds: int,
    ) -> ProviderRoom: ...

    def close_room(self, *, room_name: str) -> None: ...

    def create_participant_token(
        self,
        *,
        room_name: str,
        identity: str,
        display_name: str,
        role: str,
        ttl_seconds: int,
    ) -> ParticipantCredentials: ...

    def remove_participant(self, *, room_name: str, identity: str) -> None: ...

    def parse_webhook(
        self,
        *,
        body: str,
        authorization: str,
    ) -> ProviderWebhookEvent: ...
