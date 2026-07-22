from __future__ import annotations

import hashlib
import secrets
from dataclasses import asdict

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from apps.scheduling.exceptions import (
    TelemedicineConsentRequiredError,
    TelemedicineInvitationExpiredError,
    TelemedicineProviderUnavailableError,
)
from apps.scheduling.integrations.telemedicine import (
    TelemedicineProviderError,
    get_telemedicine_provider,
)
from apps.scheduling.models import (
    TelemedicineConsent,
    TelemedicineInvitation,
    TelemedicineRoom,
)
from apps.scheduling.selectors.telemedicine import (
    get_active_telemedicine_consent,
    invitation_token_hash,
)
from apps.scheduling.services.telemedicine_rooms import (
    ensure_e2ee_key,
    ensure_provider_room,
    open_telemedicine_room,
    validate_room_availability,
)
from apps.scheduling.telemedicine_config import get_telemedicine_config

TELEMEDICINE_CONSENT_VERSION = "2026-07-v1"
TELEMEDICINE_CONSENT_TEXT = """Ao prosseguir, declaro que fui informado(a) de que o atendimento ocorrerá por áudio e vídeo, em ambiente digital protegido, sem gravação pelo Elo Terapêutico. Compreendo que posso recusar esta modalidade e solicitar orientação sobre alternativa presencial. Comprometo-me a buscar um ambiente reservado, utilizar uma conexão confiável e comunicar ao profissional qualquer falha técnica ou risco à privacidade. Em situações de emergência, devo procurar os serviços públicos de urgência da minha região, pois esta sala não substitui atendimento emergencial."""
TELEMEDICINE_CONSENT_HASH = hashlib.sha256(
    TELEMEDICINE_CONSENT_TEXT.encode()
).hexdigest()


def _invitation_url(raw_token: str) -> str:
    base_url = settings.FRONTEND_URL.rstrip("/")
    return f"{base_url}/consulta-online/paciente#token={raw_token}"


def _serialize_public_context(invitation: TelemedicineInvitation) -> dict:
    room = invitation.room
    appointment = room.appointment
    organization = room.organization
    return {
        "room_public_id": str(room.public_id),
        "organization_name": organization.name,
        "therapist_name": appointment.therapist.full_name,
        "appointment_start": appointment.start_time,
        "appointment_end": appointment.end_time,
        "room_status": room.status,
        "invitation_expires_at": invitation.expires_at,
        "consent_version": TELEMEDICINE_CONSENT_VERSION,
        "consent_text": TELEMEDICINE_CONSENT_TEXT,
        "consent_accepted": bool(get_active_telemedicine_consent(room=room)),
        "recording_enabled": False,
        "e2ee_required": get_telemedicine_config().require_e2ee,
    }


def _get_valid_invitation(*, raw_token: str, lock: bool) -> TelemedicineInvitation:
    token_hash = invitation_token_hash(raw_token)
    queryset = TelemedicineInvitation.objects.select_related(
        "organization",
        "room",
        "room__organization",
        "room__organization__settings",
        "room__appointment",
        "room__appointment__patient",
        "room__appointment__therapist",
    )
    if lock:
        queryset = queryset.select_for_update()
    try:
        invitation = queryset.get(token_hash=token_hash)
    except TelemedicineInvitation.DoesNotExist as exc:
        raise TelemedicineInvitationExpiredError(
            "O acesso é inválido ou não está mais disponível."
        ) from exc
    if not invitation.is_valid:
        raise TelemedicineInvitationExpiredError(
            "O acesso é inválido ou não está mais disponível."
        )
    return invitation


@transaction.atomic
def create_patient_invitation(
    *,
    actor,
    room: TelemedicineRoom,
) -> tuple[TelemedicineInvitation, str, str]:
    locked_room = (
        TelemedicineRoom.objects.select_for_update()
        .select_related(
            "organization",
            "organization__settings",
            "appointment",
            "appointment__therapist",
        )
        .get(pk=room.pk)
    )
    validate_room_availability(room=locked_room, require_join_window=False)

    now = timezone.now()
    locked_room.invitations.filter(
        role=TelemedicineInvitation.Role.PATIENT,
        revoked_at__isnull=True,
    ).update(revoked_at=now, updated_at=now)

    raw_token = secrets.token_urlsafe(48)
    invitation = TelemedicineInvitation.objects.create(
        organization=locked_room.organization,
        room=locked_room,
        role=TelemedicineInvitation.Role.PATIENT,
        token_hash=invitation_token_hash(raw_token),
        expires_at=locked_room.expires_at,
        created_by=actor,
    )
    return invitation, raw_token, _invitation_url(raw_token)


@transaction.atomic
def revoke_patient_invitation(
    *,
    actor,
    room: TelemedicineRoom,
) -> TelemedicineInvitation | None:
    del actor
    invitation = (
        TelemedicineInvitation.objects.select_for_update()
        .filter(
            room=room,
            role=TelemedicineInvitation.Role.PATIENT,
            revoked_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
    if invitation:
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at", "updated_at"])
    return invitation


@transaction.atomic
def exchange_patient_invitation(*, raw_token: str) -> dict:
    invitation = _get_valid_invitation(raw_token=raw_token, lock=True)
    validate_room_availability(room=invitation.room, require_join_window=False)
    invitation.last_used_at = timezone.now()
    invitation.use_count = F("use_count") + 1
    invitation.save(update_fields=["last_used_at", "use_count", "updated_at"])
    invitation.refresh_from_db(fields=["use_count", "last_used_at"])
    return _serialize_public_context(invitation)


@transaction.atomic
def record_telemedicine_consent(
    *,
    raw_token: str,
    accepted: bool,
    responsible_guardian_name: str = "",
) -> TelemedicineConsent:
    if accepted is not True:
        raise TelemedicineConsentRequiredError(
            "É necessário aceitar o termo para entrar no atendimento."
        )
    invitation = _get_valid_invitation(raw_token=raw_token, lock=True)
    validate_room_availability(room=invitation.room, require_join_window=False)

    method = (
        TelemedicineConsent.AcceptanceMethod.RESPONSIBLE_LINK
        if responsible_guardian_name.strip()
        else TelemedicineConsent.AcceptanceMethod.PATIENT_LINK
    )
    existing = get_active_telemedicine_consent(room=invitation.room)
    if existing:
        return existing

    try:
        return TelemedicineConsent.objects.create(
            organization=invitation.organization,
            room=invitation.room,
            patient=invitation.room.appointment.patient,
            responsible_guardian_name=responsible_guardian_name.strip(),
            document_version=TELEMEDICINE_CONSENT_VERSION,
            document_hash=TELEMEDICINE_CONSENT_HASH,
            acceptance_method=method,
        )
    except IntegrityError:
        consent = get_active_telemedicine_consent(room=invitation.room)
        if consent:
            return consent
        raise


def _issue_credentials(
    *,
    room: TelemedicineRoom,
    role: str,
    display_name: str,
) -> dict:
    config = get_telemedicine_config()
    room = ensure_provider_room(room=room)
    with transaction.atomic():
        room = ensure_e2ee_key(room=room)

    identity = f"telemed:{room.public_id.hex}:{role}:{secrets.token_hex(12)}"
    provider = get_telemedicine_provider()
    try:
        credentials = provider.create_participant_token(
            room_name=room.provider_room_name,
            identity=identity,
            display_name=display_name,
            role=role,
            ttl_seconds=config.provider_token_ttl_seconds,
        )
    except TelemedicineProviderError as exc:
        raise TelemedicineProviderUnavailableError(
            "O atendimento online está temporariamente indisponível."
        ) from exc

    return {
        **asdict(credentials),
        "role": role,
        "e2ee_key": room.e2ee_key,
        "e2ee_enabled": room.e2ee_enabled,
        "expires_in": config.provider_token_ttl_seconds,
        "recording_enabled": False,
    }


def issue_patient_join_credentials(*, raw_token: str) -> dict:
    invitation = _get_valid_invitation(raw_token=raw_token, lock=False)
    validate_room_availability(room=invitation.room, require_join_window=True)
    if not get_active_telemedicine_consent(room=invitation.room):
        raise TelemedicineConsentRequiredError(
            "É necessário aceitar o termo para entrar no atendimento."
        )
    return _issue_credentials(
        room=invitation.room,
        role="patient",
        display_name="Paciente",
    )


def issue_professional_join_credentials(*, actor, room: TelemedicineRoom) -> dict:
    room = open_telemedicine_room(actor=actor, room=room)
    return _issue_credentials(
        room=room,
        role="professional",
        display_name="Profissional",
    )
