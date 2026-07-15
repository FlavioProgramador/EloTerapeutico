"""Casos de uso e selectors da fundação multi-tenant por clínica."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.users.models import AuthSession, Clinic, ClinicInvitation, ClinicMembership, User

_MANAGEMENT_ROLES = {
    ClinicMembership.Role.OWNER,
    ClinicMembership.Role.ADMIN,
}
_DEFAULT_ROLE_PRIORITY = {
    ClinicMembership.Role.OWNER: 0,
    ClinicMembership.Role.ADMIN: 1,
    ClinicMembership.Role.THERAPIST: 2,
    ClinicMembership.Role.SECRETARY: 3,
    ClinicMembership.Role.FINANCIAL: 4,
    ClinicMembership.Role.SUPPORT: 5,
}


@dataclass(frozen=True, slots=True)
class ClinicBackfillResult:
    users_scanned: int = 0
    clinics_created: int = 0
    memberships_created: int = 0
    sessions_updated: int = 0


@dataclass(frozen=True, slots=True)
class ClinicValidationResult:
    eligible_users_without_membership: tuple[int, ...]
    sessions_with_invalid_clinic: tuple[int, ...]

    @property
    def is_valid(self) -> bool:
        return not self.eligible_users_without_membership and not self.sessions_with_invalid_clinic


def active_memberships_for_user(*, user: User):
    """Retorna apenas memberships e clínicas ativas do usuário autenticado."""

    return (
        ClinicMembership.objects.select_related("clinic")
        .filter(
            user=user,
            status=ClinicMembership.Status.ACTIVE,
            clinic__status=Clinic.Status.ACTIVE,
        )
        .order_by("clinic__name", "clinic_id")
    )


def preferred_membership_for_user(*, user: User) -> ClinicMembership | None:
    memberships = list(active_memberships_for_user(user=user))
    if not memberships:
        return None
    memberships.sort(
        key=lambda membership: (
            _DEFAULT_ROLE_PRIORITY.get(membership.role, 99),
            membership.clinic_id,
        )
    )
    return memberships[0]


def membership_for_clinic(
    *,
    user: User,
    clinic_public_id: UUID | str,
    lock: bool = False,
) -> ClinicMembership:
    queryset = ClinicMembership.objects.select_related("clinic").filter(
        user=user,
        clinic__public_id=clinic_public_id,
        status=ClinicMembership.Status.ACTIVE,
        clinic__status=Clinic.Status.ACTIVE,
    )
    if lock:
        queryset = queryset.select_for_update()
    membership = queryset.first()
    if membership is None:
        raise Http404("Clínica não encontrada.")
    return membership


def resolve_active_membership(
    *,
    user: User,
    session: AuthSession | None = None,
    persist_fallback: bool = True,
) -> ClinicMembership | None:
    """Resolve a clínica ativa sem confiar em ID ou papel enviados pelo cliente."""

    if session is not None and session.active_clinic_id:
        membership = (
            active_memberships_for_user(user=user)
            .filter(clinic_id=session.active_clinic_id)
            .first()
        )
        if membership is not None:
            return membership

    fallback = preferred_membership_for_user(user=user)
    if session is not None and persist_fallback:
        fallback_clinic_id = fallback.clinic_id if fallback else None
        if session.active_clinic_id != fallback_clinic_id:
            AuthSession.objects.filter(pk=session.pk, user=user).update(
                active_clinic_id=fallback_clinic_id,
                last_seen_at=timezone.now(),
            )
            session.active_clinic_id = fallback_clinic_id
    return fallback


@transaction.atomic
def switch_active_clinic(
    *,
    user: User,
    session: AuthSession,
    clinic_public_id: UUID | str,
) -> ClinicMembership:
    """Troca somente a clínica da sessão corrente após validar membership ativo."""

    locked_session = AuthSession.objects.select_for_update().filter(
        pk=session.pk,
        user=user,
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).first()
    if locked_session is None:
        raise PermissionDenied("Sessão inválida ou expirada.")

    membership = membership_for_clinic(
        user=user,
        clinic_public_id=clinic_public_id,
        lock=True,
    )
    locked_session.active_clinic = membership.clinic
    locked_session.last_seen_at = timezone.now()
    locked_session.save(update_fields=["active_clinic", "last_seen_at"])
    session.active_clinic_id = membership.clinic_id
    return membership


def membership_can_manage_clinic(membership: ClinicMembership | None) -> bool:
    return bool(membership and membership.is_active and membership.role in _MANAGEMENT_ROLES)


def require_clinic_manager(*, actor: User, clinic: Clinic) -> ClinicMembership:
    membership = (
        ClinicMembership.objects.select_related("clinic")
        .filter(
            user=actor,
            clinic=clinic,
            status=ClinicMembership.Status.ACTIVE,
            clinic__status=Clinic.Status.ACTIVE,
            role__in=_MANAGEMENT_ROLES,
        )
        .first()
    )
    if membership is None:
        raise Http404("Clínica não encontrada.")
    return membership


def _invitation_token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_clinic_invitation(
    *,
    actor: User,
    clinic: Clinic,
    email: str,
    role: str,
    expires_in_days: int = 7,
) -> tuple[ClinicInvitation, str]:
    """Cria convite e devolve o token bruto uma única vez ao chamador."""

    require_clinic_manager(actor=actor, clinic=clinic)
    normalized_email = User.objects.normalize_email(email).strip().lower()
    if role == ClinicMembership.Role.OWNER:
        raise ValidationError("Transferência de propriedade exige um fluxo específico.")
    if role not in ClinicMembership.Role.values:
        raise ValidationError("Função de clínica inválida.")
    if ClinicMembership.objects.filter(
        clinic=clinic,
        user__email__iexact=normalized_email,
        status=ClinicMembership.Status.ACTIVE,
    ).exists():
        raise ValidationError("O usuário já possui vínculo ativo com esta clínica.")

    ClinicInvitation.objects.select_for_update().filter(
        clinic=clinic,
        email__iexact=normalized_email,
        status=ClinicInvitation.Status.PENDING,
    ).update(status=ClinicInvitation.Status.REVOKED)

    raw_token = secrets.token_urlsafe(32)
    invitation = ClinicInvitation.objects.create(
        clinic=clinic,
        email=normalized_email,
        role=role,
        token_hash=_invitation_token_hash(raw_token),
        expires_at=timezone.now() + timedelta(days=max(expires_in_days, 1)),
        invited_by=actor,
    )
    return invitation, raw_token


@transaction.atomic
def accept_clinic_invitation(*, user: User, raw_token: str) -> ClinicMembership:
    token_hash = _invitation_token_hash(raw_token)
    invitation = (
        ClinicInvitation.objects.select_for_update()
        .select_related("clinic")
        .filter(token_hash=token_hash, status=ClinicInvitation.Status.PENDING)
        .first()
    )
    if invitation is None:
        raise Http404("Convite não encontrado.")
    if invitation.is_expired:
        invitation.status = ClinicInvitation.Status.EXPIRED
        invitation.save(update_fields=["status", "updated_at"])
        raise Http404("Convite não encontrado.")
    if invitation.clinic.status != Clinic.Status.ACTIVE:
        raise Http404("Convite não encontrado.")
    if invitation.email.casefold() != user.email.casefold():
        raise Http404("Convite não encontrado.")

    membership, _ = ClinicMembership.objects.select_for_update().get_or_create(
        clinic=invitation.clinic,
        user=user,
        defaults={
            "role": invitation.role,
            "status": ClinicMembership.Status.ACTIVE,
            "joined_at": timezone.now(),
            "invited_by": invitation.invited_by,
        },
    )
    if membership.role == ClinicMembership.Role.OWNER and invitation.role != ClinicMembership.Role.OWNER:
        raise ValidationError("O vínculo existente não pode ser reduzido por convite.")
    if membership.status != ClinicMembership.Status.ACTIVE:
        membership.role = invitation.role
        membership.status = ClinicMembership.Status.ACTIVE
        membership.joined_at = membership.joined_at or timezone.now()
        membership.invited_by = invitation.invited_by
        membership.save(
            update_fields=["role", "status", "joined_at", "invited_by", "updated_at"]
        )

    invitation.status = ClinicInvitation.Status.ACCEPTED
    invitation.accepted_by = user
    invitation.accepted_at = timezone.now()
    invitation.save(
        update_fields=["status", "accepted_by", "accepted_at", "updated_at"]
    )
    return membership


def _default_clinic_name(user: Any) -> str:
    configured = str(getattr(user, "clinic_name", "") or "").strip()
    if configured:
        return configured[:160]
    display_name = str(getattr(user, "full_name", "") or "Profissional").strip()
    return f"Clínica de {display_name}"[:160]


@transaction.atomic
def ensure_default_clinic_for_user(*, user: User) -> tuple[ClinicMembership | None, bool, bool]:
    """Cria clínica padrão apenas para perfis legados elegíveis e de forma idempotente."""

    existing = preferred_membership_for_user(user=user)
    if existing is not None:
        return existing, False, False
    if user.role not in {User.Role.THERAPIST, User.Role.ADMIN}:
        return None, False, False

    clinic = Clinic.objects.create(
        name=_default_clinic_name(user),
        email=user.email,
        phone=user.phone,
        address=user.professional_address or {},
        timezone="America/Sao_Paulo",
    )
    membership = ClinicMembership.objects.create(
        clinic=clinic,
        user=user,
        role=ClinicMembership.Role.OWNER,
        status=ClinicMembership.Status.ACTIVE,
        joined_at=timezone.now(),
    )
    return membership, True, True


@transaction.atomic
def backfill_default_clinics(*, user_ids: list[int] | None = None) -> ClinicBackfillResult:
    queryset = User.objects.filter(is_active=True).order_by("pk")
    if user_ids is not None:
        queryset = queryset.filter(pk__in=user_ids)

    users_scanned = clinics_created = memberships_created = sessions_updated = 0
    for user in queryset.iterator(chunk_size=200):
        users_scanned += 1
        membership, clinic_created, membership_created = ensure_default_clinic_for_user(user=user)
        clinics_created += int(clinic_created)
        memberships_created += int(membership_created)
        if membership is None:
            continue
        sessions_updated += AuthSession.objects.filter(
            user=user,
            active_clinic__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).update(active_clinic=membership.clinic)

    return ClinicBackfillResult(
        users_scanned=users_scanned,
        clinics_created=clinics_created,
        memberships_created=memberships_created,
        sessions_updated=sessions_updated,
    )


def validate_clinic_foundation() -> ClinicValidationResult:
    eligible_ids = tuple(
        User.objects.filter(
            is_active=True,
            role__in=[User.Role.THERAPIST, User.Role.ADMIN],
        )
        .exclude(
            clinic_memberships__status=ClinicMembership.Status.ACTIVE,
            clinic_memberships__clinic__status=Clinic.Status.ACTIVE,
        )
        .order_by("pk")
        .values_list("pk", flat=True)
    )
    invalid_session_ids = tuple(
        AuthSession.objects.filter(active_clinic__isnull=False)
        .exclude(
            active_clinic__memberships__user_id=models_outer_user_id_placeholder(),
        )
        .values_list("pk", flat=True)
    )
    return ClinicValidationResult(
        eligible_users_without_membership=eligible_ids,
        sessions_with_invalid_clinic=invalid_session_ids,
    )


def models_outer_user_id_placeholder():
    """Separado para permitir uso de F sem esconder a intenção da validação."""

    from django.db.models import F

    return F("user_id")
