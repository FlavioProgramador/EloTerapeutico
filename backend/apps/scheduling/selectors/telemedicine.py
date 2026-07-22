"""Selectors de acesso a salas e convites de telemedicina."""

from __future__ import annotations

import hashlib

from django.shortcuts import get_object_or_404

from apps.scheduling.models import (
    TelemedicineConsent,
    TelemedicineInvitation,
    TelemedicineRoom,
)


def invitation_token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def get_telemedicine_invitation_by_token(*, raw_token: str) -> TelemedicineInvitation:
    return get_object_or_404(
        TelemedicineInvitation.objects.select_related(
            "organization",
            "room",
            "room__appointment",
            "room__appointment__patient",
            "room__appointment__therapist",
        ),
        token_hash=invitation_token_hash(raw_token),
    )


def get_active_telemedicine_consent(*, room: TelemedicineRoom):
    return (
        TelemedicineConsent.objects.filter(room=room, revoked_at__isnull=True)
        .order_by("-accepted_at")
        .first()
    )


def get_telemedicine_room_by_provider_name(*, room_name: str):
    return (
        TelemedicineRoom.objects.select_related(
            "organization",
            "appointment",
            "appointment__patient",
            "appointment__therapist",
        )
        .filter(provider_room_name=room_name)
        .first()
    )


def get_telemedicine_room_by_token(*, role: str, token):
    """Compatibilidade temporária para links legados já invalidados."""

    token_field = "patient_token" if role == "patient" else "professional_token"
    return get_object_or_404(
        TelemedicineRoom.objects.select_related(
            "organization",
            "appointment",
            "appointment__patient",
            "appointment__therapist",
        ),
        **{token_field: token},
    )


__all__ = [
    "get_active_telemedicine_consent",
    "get_telemedicine_invitation_by_token",
    "get_telemedicine_room_by_provider_name",
    "get_telemedicine_room_by_token",
    "invitation_token_hash",
]
