from __future__ import annotations

import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Subscription
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability
from apps.scheduling.exceptions import (
    TelemedicineAccessDeniedError,
    TelemedicineDisabledError,
    TelemedicineEncryptionUnavailableError,
    TelemedicineInvalidStateError,
    TelemedicineOutsideJoinWindowError,
    TelemedicineProviderUnavailableError,
)
from apps.scheduling.integrations.telemedicine import (
    TelemedicineProviderError,
    get_telemedicine_provider,
)
from apps.scheduling.models import Appointment, TelemedicineRoom
from apps.scheduling.telemedicine_config import get_telemedicine_config


def _organization_allows_telemedicine(room: TelemedicineRoom) -> bool:
    organization_settings = getattr(room.organization, "settings", None)
    return bool(organization_settings and organization_settings.allow_telemedicine)


def _plan_allows_telemedicine(room: TelemedicineRoom) -> bool:
    subscription = (
        Subscription.objects.select_related("plan")
        .filter(
            user=room.appointment.therapist,
            status__in=[
                Subscription.Status.TRIALING,
                Subscription.Status.ACTIVE,
                Subscription.Status.PAST_DUE,
            ],
        )
        .order_by("-created_at")
        .first()
    )
    return bool(
        subscription
        and subscription.has_access
        and subscription.plan.has_telemedicine
    )


def validate_room_availability(
    *,
    room: TelemedicineRoom,
    require_join_window: bool,
) -> None:
    config = get_telemedicine_config()
    if not config.enabled or not _organization_allows_telemedicine(room):
        raise TelemedicineDisabledError(
            "O atendimento online ainda não está disponível para esta organização."
        )
    if not config.provider_configured:
        raise TelemedicineProviderUnavailableError(
            "O atendimento online está temporariamente indisponível."
        )
    if not _plan_allows_telemedicine(room):
        raise TelemedicineAccessDeniedError(
            "O plano atual não inclui atendimento online."
        )

    appointment = room.appointment
    if appointment.modality not in {
        Appointment.Modality.ONLINE,
        Appointment.Modality.HYBRID,
    }:
        raise TelemedicineInvalidStateError(
            "Esta consulta não está configurada para atendimento online."
        )
    if appointment.status in {
        Appointment.Status.CANCELLED,
        Appointment.Status.COMPLETED,
        Appointment.Status.MISSED,
    }:
        raise TelemedicineInvalidStateError(
            "O atendimento não pode ser iniciado neste estado."
        )
    if not room.is_accessible:
        raise TelemedicineInvalidStateError(
            "A sala expirou, foi revogada ou já foi encerrada."
        )

    if require_join_window:
        now = timezone.now()
        opens_at = appointment.start_time - timedelta(
            minutes=config.join_before_minutes
        )
        closes_at = appointment.end_time + timedelta(
            minutes=config.join_after_minutes
        )
        if now < opens_at or now > closes_at:
            raise TelemedicineOutsideJoinWindowError(
                "A sala ainda não está disponível ou a janela de acesso terminou."
            )


def validate_professional_access(*, actor, room: TelemedicineRoom) -> None:
    membership = (
        OrganizationMembership.objects.filter(
            organization=room.organization,
            user=actor,
            status=OrganizationMembership.Status.ACTIVE,
        )
        .select_related("organization", "user")
        .first()
    )
    allowed_role = bool(
        membership
        and membership.role
        in {
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        }
    )
    responsible_therapist = actor.pk == room.appointment.therapist_id
    if not (
        membership
        and has_capability(membership, "scheduling.view")
        and (allowed_role or responsible_therapist)
    ):
        raise TelemedicineAccessDeniedError(
            "Você não possui acesso a este atendimento."
        )


def ensure_e2ee_key(*, room: TelemedicineRoom) -> TelemedicineRoom:
    config = get_telemedicine_config()
    locked = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
    if not locked.e2ee_key:
        locked.e2ee_key = secrets.token_urlsafe(32)
        locked.e2ee_enabled = True
        locked.save(update_fields=["e2ee_key", "e2ee_enabled", "updated_at"])
    if config.require_e2ee and not locked.e2ee_key:
        raise TelemedicineEncryptionUnavailableError(
            "Não foi possível iniciar a chamada com segurança."
        )
    return locked


def ensure_provider_room(*, room: TelemedicineRoom) -> TelemedicineRoom:
    validate_room_availability(room=room, require_join_window=False)
    if room.provider_room_sid:
        return room

    config = get_telemedicine_config()
    provider = get_telemedicine_provider()
    try:
        provider_room = provider.create_room(
            room_name=room.provider_room_name,
            max_participants=config.max_participants,
            empty_timeout_seconds=config.empty_room_timeout_seconds,
        )
    except TelemedicineProviderError as exc:
        TelemedicineRoom.objects.filter(pk=room.pk).update(
            status=TelemedicineRoom.Status.FAILED,
            failure_code="provider_room_create_failed",
            ended_at=timezone.now(),
            updated_at=timezone.now(),
        )
        raise TelemedicineProviderUnavailableError(
            "O atendimento online está temporariamente indisponível."
        ) from exc

    with transaction.atomic():
        locked = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
        locked.provider_room_sid = provider_room.sid
        locked.failure_code = ""
        if locked.status == TelemedicineRoom.Status.PENDING:
            locked.transition_to(TelemedicineRoom.Status.AVAILABLE, save=False)
        locked.save()
        return locked


def open_telemedicine_room(*, actor, room: TelemedicineRoom) -> TelemedicineRoom:
    validate_professional_access(actor=actor, room=room)
    validate_room_availability(room=room, require_join_window=True)
    room = ensure_provider_room(room=room)
    with transaction.atomic():
        locked = ensure_e2ee_key(room=room)
        if locked.status == TelemedicineRoom.Status.AVAILABLE:
            locked.transition_to(TelemedicineRoom.Status.WAITING)
        return locked


def finish_telemedicine_room(*, actor, room: TelemedicineRoom) -> TelemedicineRoom:
    validate_professional_access(actor=actor, room=room)
    provider = get_telemedicine_provider()
    try:
        provider.close_room(room_name=room.provider_room_name)
    except TelemedicineProviderError:
        # O domínio ainda precisa ser fechado; a reconciliação operacional pode
        # tentar novamente sem manter o paciente com acesso válido.
        pass

    with transaction.atomic():
        locked = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
        if locked.status not in locked.TERMINAL_STATUSES:
            locked.transition_to(TelemedicineRoom.Status.FINISHED, save=False)
        locked.revoked_at = timezone.now()
        locked.closed_by = actor
        locked.save()
        locked.invitations.filter(revoked_at__isnull=True).update(
            revoked_at=timezone.now(),
            updated_at=timezone.now(),
        )
        return locked


def remove_telemedicine_participant(
    *,
    actor,
    room: TelemedicineRoom,
    identity: str,
) -> None:
    validate_professional_access(actor=actor, room=room)
    if not identity.startswith(f"telemed:{room.public_id.hex}:"):
        raise TelemedicineAccessDeniedError("Participante inválido para esta sala.")
    provider = get_telemedicine_provider()
    try:
        provider.remove_participant(
            room_name=room.provider_room_name,
            identity=identity,
        )
    except TelemedicineProviderError as exc:
        raise TelemedicineProviderUnavailableError(
            "Não foi possível remover o participante."
        ) from exc


def expire_telemedicine_rooms(*, batch_size: int = 100) -> int:
    now = timezone.now()
    expired_ids = list(
        TelemedicineRoom.objects.filter(
            expires_at__lte=now,
            revoked_at__isnull=True,
            status__in=[
                TelemedicineRoom.Status.PENDING,
                TelemedicineRoom.Status.AVAILABLE,
                TelemedicineRoom.Status.WAITING,
            ],
        )
        .order_by("expires_at")
        .values_list("pk", flat=True)[:batch_size]
    )
    if not expired_ids:
        return 0

    with transaction.atomic():
        rooms = TelemedicineRoom.objects.select_for_update().filter(
            pk__in=expired_ids
        )
        count = 0
        for room in rooms:
            if room.status not in room.TERMINAL_STATUSES:
                room.transition_to(TelemedicineRoom.Status.EXPIRED, save=False)
            room.revoked_at = now
            room.save()
            room.invitations.filter(revoked_at__isnull=True).update(
                revoked_at=now,
                updated_at=now,
            )
            count += 1
        return count
