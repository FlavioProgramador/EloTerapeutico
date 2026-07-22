from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProviderRoom:
    name: str
    sid: str = ""


@dataclass(frozen=True, slots=True)
class ParticipantCredentials:
    server_url: str
    token: str
    identity: str
    room_name: str


@dataclass(frozen=True, slots=True)
class ProviderWebhookEvent:
    event_id: str
    event_type: str
    room_name: str = ""
    room_sid: str = ""
    participant_identity: str = ""
    participant_sid: str = ""
    occurred_at: datetime | None = None
    disconnect_reason: str = ""
