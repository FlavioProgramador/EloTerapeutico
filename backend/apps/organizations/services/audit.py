"""Adapter mínimo e seguro para a trilha de auditoria existente."""

from __future__ import annotations

from collections.abc import Mapping

from apps.audit.models import AuditLog
from apps.audit.services.events import record_audit_event


def audit_organization_action(
    *,
    action: str,
    actor,
    organization,
    request=None,
    metadata: Mapping[str, object] | None = None,
) -> None:
    record_audit_event(
        action=getattr(AuditLog.Action, action),
        actor=actor,
        request=request,
        resource_repr=f"Organização {organization.pk}",
        metadata={"organization_id": str(organization.pk), **(metadata or {})},
        source="organizations",
    )
