from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from asgiref.sync import async_to_sync
from django.conf import settings
from livekit import api

from .exceptions import (
    TelemedicineProviderConfigurationError,
    TelemedicineProviderError,
    TelemedicineWebhookVerificationError,
)
from .types import ParticipantCredentials, ProviderRoom, ProviderWebhookEvent


class LiveKitTelemedicineProvider:
    """Adapta o SDK oficial do LiveKit ao domínio de scheduling."""

    @property
    def configured(self) -> bool:
        return all(
            [
                getattr(settings, "LIVEKIT_URL", ""),
                getattr(settings, "LIVEKIT_API_KEY", ""),
                getattr(settings, "LIVEKIT_API_SECRET", ""),
            ]
        )

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise TelemedicineProviderConfigurationError(
                "O provedor de atendimento online não está disponível."
            )

    async def _create_room(
        self,
        *,
        room_name: str,
        max_participants: int,
        empty_timeout_seconds: int,
    ) -> ProviderRoom:
        client = api.LiveKitAPI(
            getattr(settings, "LIVEKIT_URL", ""),
            getattr(settings, "LIVEKIT_API_KEY", ""),
            getattr(settings, "LIVEKIT_API_SECRET", ""),
        )
        try:
            room = await client.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    max_participants=max_participants,
                    empty_timeout=empty_timeout_seconds,
                )
            )
            return ProviderRoom(name=room.name, sid=room.sid)
        finally:
            await client.aclose()

    def create_room(
        self,
        *,
        room_name: str,
        max_participants: int,
        empty_timeout_seconds: int,
    ) -> ProviderRoom:
        self._ensure_configured()
        try:
            return async_to_sync(self._create_room)(
                room_name=room_name,
                max_participants=max_participants,
                empty_timeout_seconds=empty_timeout_seconds,
            )
        except TelemedicineProviderError:
            raise
        except Exception as exc:
            raise TelemedicineProviderError(
                "Não foi possível preparar a sala de atendimento."
            ) from exc

    async def _close_room(self, *, room_name: str) -> None:
        client = api.LiveKitAPI(
            getattr(settings, "LIVEKIT_URL", ""),
            getattr(settings, "LIVEKIT_API_KEY", ""),
            getattr(settings, "LIVEKIT_API_SECRET", ""),
        )
        try:
            await client.room.delete_room(api.DeleteRoomRequest(room=room_name))
        finally:
            await client.aclose()

    def close_room(self, *, room_name: str) -> None:
        self._ensure_configured()
        try:
            async_to_sync(self._close_room)(room_name=room_name)
        except Exception as exc:
            message = str(exc).lower()
            if "not_found" in message or "does not exist" in message:
                return
            raise TelemedicineProviderError(
                "Não foi possível encerrar a sala de atendimento."
            ) from exc

    def create_participant_token(
        self,
        *,
        room_name: str,
        identity: str,
        display_name: str,
        role: str,
        ttl_seconds: int,
    ) -> ParticipantCredentials:
        self._ensure_configured()
        try:
            token = (
                api.AccessToken(
                    getattr(settings, "LIVEKIT_API_KEY", ""),
                    getattr(settings, "LIVEKIT_API_SECRET", ""),
                )
                .with_identity(identity)
                .with_name(display_name)
                .with_metadata(json.dumps({"role": role}, separators=(",", ":")))
                .with_ttl(timedelta(seconds=ttl_seconds))
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_publish_data=False,
                        can_subscribe=True,
                        room_record=False,
                    )
                )
                .to_jwt()
            )
            return ParticipantCredentials(
                server_url=getattr(settings, "LIVEKIT_URL", ""),
                token=token,
                identity=identity,
                room_name=room_name,
            )
        except Exception as exc:
            raise TelemedicineProviderError(
                "Não foi possível autorizar o acesso à chamada."
            ) from exc

    async def _remove_participant(self, *, room_name: str, identity: str) -> None:
        client = api.LiveKitAPI(
            getattr(settings, "LIVEKIT_URL", ""),
            getattr(settings, "LIVEKIT_API_KEY", ""),
            getattr(settings, "LIVEKIT_API_SECRET", ""),
        )
        try:
            await client.room.remove_participant(
                api.RoomParticipantIdentity(room=room_name, identity=identity)
            )
        finally:
            await client.aclose()

    def remove_participant(self, *, room_name: str, identity: str) -> None:
        self._ensure_configured()
        try:
            async_to_sync(self._remove_participant)(
                room_name=room_name,
                identity=identity,
            )
        except Exception as exc:
            raise TelemedicineProviderError(
                "Não foi possível remover o participante."
            ) from exc

    def parse_webhook(
        self,
        *,
        body: str,
        authorization: str,
    ) -> ProviderWebhookEvent:
        self._ensure_configured()
        try:
            receiver = api.WebhookReceiver(
                api.TokenVerifier(
                    getattr(settings, "LIVEKIT_API_KEY", ""),
                    getattr(settings, "LIVEKIT_API_SECRET", ""),
                )
            )
            event = receiver.receive(body, authorization)
        except Exception as exc:
            raise TelemedicineWebhookVerificationError(
                "Assinatura de webhook inválida."
            ) from exc

        created_at = getattr(event, "created_at", 0) or 0
        occurred_at = (
            datetime.fromtimestamp(created_at, tz=timezone.utc)
            if created_at
            else None
        )
        room = getattr(event, "room", None)
        participant = getattr(event, "participant", None)
        return ProviderWebhookEvent(
            event_id=str(getattr(event, "id", "")),
            event_type=str(getattr(event, "event", "")),
            room_name=str(getattr(room, "name", "")),
            room_sid=str(getattr(room, "sid", "")),
            participant_identity=str(getattr(participant, "identity", "")),
            participant_sid=str(getattr(participant, "sid", "")),
            occurred_at=occurred_at,
            disconnect_reason=str(getattr(event, "reason", "")),
        )
