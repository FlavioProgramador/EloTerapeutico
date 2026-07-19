"""Compatibilidade: registros administrativos movidos para scheduling."""

from apps.scheduling import admin as scheduling_admin

__all__ = ["scheduling_admin"]
