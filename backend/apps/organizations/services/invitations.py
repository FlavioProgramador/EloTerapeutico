"""Casos de uso de convites com token persistido somente como hash."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.organizations.exceptions import (
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationInvalidError,
)
from apps.organizations.integrations.communications import enqueue_invitation_email
from apps.organizations.models import OrganizationInvitation, OrganizationMembership
from apps.organizations.selectors import get_invitation_by_hash

from .audit import audit_organization_action


def hash_invitation_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_invitation(
    *, actor, organization, email: str, role: str, request=None
) -> tuple[OrganizationInvitation, str]:
    normalized_email = email.strip().lower()
    if role == OrganizationMembership.Role.OWNER:
        actor_membership = OrganizationMembership.objects.get(
            organization=organization,
            user=actor,
            status=OrganizationMembership.Status.ACTIVE,
        )
        if actor_membership.role != OrganizationMembership.Role.OWNER:
            raise PermissionError("Somente um proprietário pode convidar outro proprietário.")
    if OrganizationMembership.objects.filter(
        organization=organization,
        user__email__iexact=normalized_email,
    ).exclude(status=OrganizationMembership.Status.REVOKED).exists():
        raise ValueError("Este usuário já pertence à organização.")

    raw_token = secrets.token_urlsafe(48)
    invitation = OrganizationInvitation.objects.create(
        organization=organization,
        email=normalized_email,
        role=role,
        token_hash=hash_invitation_token(raw_token),
        expires_at=timezone.now() + timedelta(days=7),
        invited_by=actor,
    )
    transaction.on_commit(
        lambda: enqueue_invitation_email(invitation=invitation, raw_token=raw_token)
    )
    audit_organization_action(
        action="CREATE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"invitation_id": str(invitation.pk), "role": role},
    )
    return invitation, raw_token


@transaction.atomic
def resend_invitation(
    *, actor, invitation: OrganizationInvitation, request=None
) -> tuple[OrganizationInvitation, str]:
    locked = OrganizationInvitation.objects.select_for_update().get(pk=invitation.pk)
    if locked.status != OrganizationInvitation.Status.PENDING:
        raise InvitationAlreadyUsedError()
    raw_token = secrets.token_urlsafe(48)
    locked.token_hash = hash_invitation_token(raw_token)
    locked.expires_at = timezone.now() + timedelta(days=7)
    locked.save(update_fields=["token_hash", "expires_at", "updated_at"])
    transaction.on_commit(
        lambda: enqueue_invitation_email(invitation=locked, raw_token=raw_token)
    )
    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=locked.organization,
        request=request,
        metadata={"invitation_id": str(locked.pk), "resent": True},
    )
    return locked, raw_token


@transaction.atomic
def revoke_invitation(*, actor, invitation: OrganizationInvitation, request=None):
    locked = OrganizationInvitation.objects.select_for_update().get(pk=invitation.pk)
    if locked.status != OrganizationInvitation.Status.PENDING:
        raise InvitationAlreadyUsedError()
    locked.status = OrganizationInvitation.Status.REVOKED
    locked.revoked_at = timezone.now()
    locked.save(update_fields=["status", "revoked_at", "updated_at"])
    audit_organization_action(
        action="DELETE",
        actor=actor,
        organization=locked.organization,
        request=request,
        metadata={"invitation_id": str(locked.pk), "soft_delete": True},
    )
    return locked


@transaction.atomic
def accept_invitation(*, actor, raw_token: str, request=None) -> OrganizationMembership:
    token_hash = hash_invitation_token(raw_token)
    try:
        invitation = get_invitation_by_hash(token_hash=token_hash)
    except OrganizationInvitation.DoesNotExist as exc:
        raise InvitationInvalidError() from exc

    locked = OrganizationInvitation.objects.select_for_update().get(pk=invitation.pk)
    if locked.status != OrganizationInvitation.Status.PENDING:
        raise InvitationAlreadyUsedError()
    if locked.expires_at <= timezone.now():
        locked.status = OrganizationInvitation.Status.EXPIRED
        locked.save(update_fields=["status", "updated_at"])
        raise InvitationExpiredError()
    if actor.email.casefold() != locked.email.casefold():
        raise InvitationInvalidError()

    membership, _ = OrganizationMembership.objects.update_or_create(
        organization=locked.organization,
        user=actor,
        defaults={
            "role": locked.role,
            "status": OrganizationMembership.Status.ACTIVE,
            "invited_by": locked.invited_by,
            "joined_at": timezone.now(),
        },
    )
    if not OrganizationMembership.objects.filter(user=actor, is_default=True).exists():
        membership.is_default = True
        membership.save(update_fields=["is_default", "updated_at"])

    locked.status = OrganizationInvitation.Status.ACCEPTED
    locked.accepted_by = actor
    locked.accepted_at = timezone.now()
    locked.save(
        update_fields=["status", "accepted_by", "accepted_at", "updated_at"]
    )
    audit_organization_action(
        action="CREATE",
        actor=actor,
        organization=locked.organization,
        request=request,
        metadata={"membership_id": str(membership.pk)},
    )
    return membership


def expire_invitations() -> int:
    return OrganizationInvitation.objects.filter(
        status=OrganizationInvitation.Status.PENDING,
        expires_at__lte=timezone.now(),
    ).update(status=OrganizationInvitation.Status.EXPIRED)
