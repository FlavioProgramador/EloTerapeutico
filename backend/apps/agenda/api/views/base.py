"""Compatibilidade para permission e mixin de escopo."""

from apps.scheduling.api.v1.permissions import AgendaPermission
from apps.scheduling.api.views.base import ScopedAgendaMixin

__all__ = ["AgendaPermission", "ScopedAgendaMixin"]
