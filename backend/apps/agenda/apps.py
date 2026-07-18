"""Configuração legada que aponta para o app canônico ``scheduling``."""

from apps.scheduling.apps import SchedulingConfig


class AgendaConfig(SchedulingConfig):
    """Alias de compatibilidade para instalações que ainda usam ``apps.agenda``."""


__all__ = ["AgendaConfig"]
