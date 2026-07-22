from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class TelemedicineConfig:
    enabled: bool
    provider: str
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    require_e2ee: bool
    join_before_minutes: int
    join_after_minutes: int
    provider_token_ttl_seconds: int
    empty_room_timeout_seconds: int
    max_participants: int

    @property
    def provider_configured(self) -> bool:
        if self.provider == "fake":
            return True
        if self.provider != "livekit":
            return False
        return all(
            [
                self.livekit_url,
                self.livekit_api_key,
                self.livekit_api_secret,
            ]
        )


def get_telemedicine_config() -> TelemedicineConfig:
    return TelemedicineConfig(
        enabled=_as_bool("TELEMEDICINE_ENABLED", False),
        provider=os.getenv("TELEMEDICINE_PROVIDER", "livekit").strip().lower(),
        livekit_url=os.getenv("LIVEKIT_URL", "").strip(),
        livekit_api_key=os.getenv("LIVEKIT_API_KEY", "").strip(),
        livekit_api_secret=os.getenv("LIVEKIT_API_SECRET", "").strip(),
        require_e2ee=_as_bool("TELEMEDICINE_REQUIRE_E2EE", True),
        join_before_minutes=max(_as_int("TELEMEDICINE_JOIN_BEFORE_MINUTES", 15), 0),
        join_after_minutes=max(_as_int("TELEMEDICINE_JOIN_AFTER_MINUTES", 30), 0),
        provider_token_ttl_seconds=max(
            _as_int("TELEMEDICINE_PROVIDER_TOKEN_TTL_SECONDS", 300),
            60,
        ),
        empty_room_timeout_seconds=max(
            _as_int("TELEMEDICINE_EMPTY_ROOM_TIMEOUT_SECONDS", 300),
            60,
        ),
        max_participants=max(_as_int("TELEMEDICINE_MAX_PARTICIPANTS", 2), 2),
    )
