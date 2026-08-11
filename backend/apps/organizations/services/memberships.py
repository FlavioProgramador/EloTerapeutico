"""Casos de uso de memberships e transferência de propriedade."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.organizations.exceptions import LastOwnerRemovalError
from apps.organizations.models import OrganizationMembership, ProfessionalProfile

from .audit import audit_organization_action


def _active_owner_count(organization) -> int:
    return OrganizationMembership.objects.filter(
        organization=organization,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    ).count()


@transaction.atomic
def update_membership(
    *, actor, membership: OrganizationMembership, data: dict, request=None
) -> OrganizationMembership:
    locked = OrganizationMembership.objects.select_for_update().get(pk=membership.pk)
    new_role = data.get("role", locked.role)
    new_status = data.get("status", locked.status)
    removes_owner = (
        locked.role == OrganizationMembership.Role.OWNER
        and locked.status == OrganizationMembership.Status.ACTIVE
        and (
            new_role != OrganizationMembership.Role.OWNER
            or new_status != OrganizationMembership.Status.ACTIVE
        )
    )
    if removes_owner and _active_owner_count(locked.organization) <= 1:
        raise LastOwnerRemovalError()

    locked.role = new_role
    locked.status = new_status
    if new_status == OrganizationMembership.Status.ACTIVE and locked.joined_at is None:
        locked.joined_at = timezone.now()
    if new_status != OrganizationMembership.Status.ACTIVE:
        locked.is_default = False
    locked.save(
        update_fields=["role", "status", "joined_at", "is_default", "updated_at"]
    )
    if new_role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.THERAPIST,
    }:
        ProfessionalProfile.objects.get_or_create(
            membership=locked,
            defaults={"display_name": locked.user.full_name},
        )
    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=locked.organization,
        request=request,
        metadata={"membership_id": str(locked.pk), "role": locked.role},
    )
    return locked


@transaction.atomic
def remove_membership(
    *, actor, membership: OrganizationMembership, request=None
) -> OrganizationMembership:
    locked = OrganizationMembership.objects.select_for_update().get(pk=membership.pk)
    if (
        locked.role == OrganizationMembership.Role.OWNER
        and locked.status == OrganizationMembership.Status.ACTIVE
        and _active_owner_count(locked.organization) <= 1
    ):
        raise LastOwnerRemovalError()
    locked.status = OrganizationMembership.Status.REVOKED
    locked.is_default = False
    locked.save(update_fields=["status", "is_default", "updated_at"])
    audit_organization_action(
        action="DELETE",
        actor=actor,
        organization=locked.organization,
        request=request,
        metadata={"membership_id": str(locked.pk), "soft_delete": True},
    )
    return locked


@transaction.atomic
def transfer_ownership(
    *, actor, current_membership: OrganizationMembership, target: OrganizationMembership, request=None
) -> OrganizationMembership:
    if current_membership.user_id == target.user_id:
        raise ValueError("Selecione outro membro para receber a propriedade.")
    if current_membership.role != OrganizationMembership.Role.OWNER:
        raise PermissionError("Somente um proprietário pode transferir a propriedade.")
    if target.organization_id != current_membership.organization_id or not target.is_active:
        raise ValueError("O membro de destino não está ativo nesta organização.")

    current = OrganizationMembership.objects.select_for_update().get(
        pk=current_membership.pk
    )
    destination = OrganizationMembership.objects.select_for_update().get(pk=target.pk)
    destination.role = OrganizationMembership.Role.OWNER
    destination.save(update_fields=["role", "updated_at"])
    current.role = OrganizationMembership.Role.ADMIN
    current.save(update_fields=["role", "updated_at"])
    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=current.organization,
        request=request,
        metadata={"ownership_transferred_to": str(destination.user_id)},
    )
    return destination
