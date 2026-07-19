"""Configuração legada que aponta para o app canônico ``scheduling``."""

from apps.scheduling import apps as scheduling_apps


class AgendaConfig(scheduling_apps.SchedulingConfig):
    """Alias de compatibilidade para instalações que ainda usam ``apps.agenda``."""


__all__ = ["AgendaConfig"]
