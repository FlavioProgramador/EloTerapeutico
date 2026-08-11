from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timezone

from .types import ParticipantCredentials, ProviderRoom, ProviderWebhookEvent


class FakeTelemedicineProvider:
    """Provider determinístico para testes e desenvolvimento sem mídia real."""

    server_url = "wss://fake.telemedicine.invalid"

    @property
    def configured(self) -> bool:
        return True

    def create_room(
        self,
        *,
        room_name: str,
        max_participants: int,
        empty_timeout_seconds: int,
    ) -> ProviderRoom:
        del max_participants, empty_timeout_seconds
        return ProviderRoom(name=room_name, sid=f"RM_{room_name[-16:]}")

    def close_room(self, *, room_name: str) -> None:
        del room_name

    def create_participant_token(
        self,
        *,
        room_name: str,
        identity: str,
        display_name: str,
        role: str,
        ttl_seconds: int,
    ) -> ParticipantCredentials:
        payload = f"{room_name}:{identity}:{display_name}:{role}:{ttl_seconds}"
        token = f"fake.{hashlib.sha256(payload.encode()).hexdigest()}"
        return ParticipantCredentials(
            server_url=self.server_url,
            token=token,
            identity=identity,
            room_name=room_name,
        )

    def remove_participant(self, *, room_name: str, identity: str) -> None:
        del room_name, identity

    def parse_webhook(
        self,
        *,
        body: str,
        authorization: str,
    ) -> ProviderWebhookEvent:
        del authorization
        payload = json.loads(body)
        occurred_at = payload.get("occurred_at")
        return ProviderWebhookEvent(
            event_id=str(payload["id"]),
            event_type=str(payload["event"]),
            room_name=str(payload.get("room_name", "")),
            room_sid=str(payload.get("room_sid", "")),
            participant_identity=str(payload.get("participant_identity", "")),
            participant_sid=str(payload.get("participant_sid", "")),
            occurred_at=(
                datetime.fromisoformat(occurred_at).astimezone(UTC)
                if occurred_at
                else None
            ),
            disconnect_reason=str(payload.get("disconnect_reason", "")),
        )
