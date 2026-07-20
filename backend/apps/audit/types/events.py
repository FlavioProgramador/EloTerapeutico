"""Contratos tipados dos eventos de auditoria."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class AuditRequestContext:
    ip_address: str | None
    user_agent: str
    request_id: str | None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    actor: Any | None = None
    resource: Any | None = None
    resource_label: str | None = None
    resource_id: int | None = None
    resource_repr: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
    reason: str | None = None
    source: str = "application"
    request: Any | None = None


@dataclass(frozen=True, slots=True)
class AuditWritePolicy:
    fail_closed_for: frozenset[str] = frozenset()
    fail_open_for: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class AuditWriteResult:
    scheduled: bool
    audit_log: Any | None = None


__all__ = [
    "AuditEvent",
    "AuditRequestContext",
    "AuditWritePolicy",
    "AuditWriteResult",
]
