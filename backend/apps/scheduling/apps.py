"""Configuração canônica do domínio de agendamentos."""

from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    """Registra o pacote Python inglês preservando o label histórico."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scheduling"
    label = "agenda"
    verbose_name = "Agenda"
