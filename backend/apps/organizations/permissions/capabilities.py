"""Matriz centralizada de capacidades por papel."""

from __future__ import annotations

from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import OrganizationMembership

CAPABILITIES = {
    "organization.view",
    "organization.update",
    "organization.manage_members",
    "organization.manage_invitations",
    "organization.manage_settings",
    "organization.manage_billing",
    "organization.transfer_ownership",
    "patients.view",
    "patients.create",
    "patients.update",
    "patients.archive",
    "scheduling.view",
    "scheduling.manage",
    "records.view",
    "records.create",
    "records.update",
    "records.export",
    "records.view_confidential",
    "finances.view",
    "finances.manage",
    "documents.view",
    "documents.manage",
    "forms.view",
    "forms.manage",
    "communications.view",
    "communications.manage",
    "reports.view",
    "reports.export",
}

ROLE_CAPABILITIES: dict[str, frozenset[str]] = {
    OrganizationMembership.Role.OWNER: frozenset(CAPABILITIES),
    OrganizationMembership.Role.ADMIN: frozenset(
        CAPABILITIES
        - {
            "organization.transfer_ownership",
            "records.view_confidential",
        }
    ),
    OrganizationMembership.Role.THERAPIST: frozenset(
        {
            "organization.view",
            "patients.view",
            "patients.create",
            "patients.update",
            "scheduling.view",
            "scheduling.manage",
            "records.view",
            "records.create",
            "records.update",
            "records.export",
            "finances.view",
            "finances.manage",
            "documents.view",
            "documents.manage",
            "forms.view",
            "forms.manage",
            "communications.view",
            "communications.manage",
            "reports.view",
        }
    ),
    OrganizationMembership.Role.RECEPTIONIST: frozenset(
        {
            "organization.view",
            "patients.view",
            "patients.create",
            "patients.update",
            "scheduling.view",
            "scheduling.manage",
            "communications.view",
            "communications.manage",
        }
    ),
    OrganizationMembership.Role.FINANCE: frozenset(
        {
            "organization.view",
            "patients.view",
            "finances.view",
            "finances.manage",
            "reports.view",
            "reports.export",
        }
    ),
    OrganizationMembership.Role.VIEWER: frozenset(
        {
            "organization.view",
            "patients.view",
            "scheduling.view",
            "documents.view",
            "forms.view",
            "communications.view",
            "reports.view",
        }
    ),
}


def has_capability(membership: OrganizationMembership | None, capability: str) -> bool:
    if capability not in CAPABILITIES or membership is None or not membership.is_active:
        return False
    return capability in ROLE_CAPABILITIES.get(membership.role, frozenset())


def require_capability(membership: OrganizationMembership | None, capability: str) -> None:
    if not has_capability(membership, capability):
        raise PermissionDenied("Você não possui permissão para executar esta ação.")
