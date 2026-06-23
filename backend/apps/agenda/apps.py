"""
apps/agenda/apps.py
Configuração do app de agenda de consultas.
"""

from django.apps import AppConfig


class AgendaConfig(AppConfig):
    """Configuração do app de Agenda."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agenda"
    verbose_name = "Agenda"

    def ready(self):
        """Importa os signals ao inicializar o app."""
        # Importação lazy para registrar os signals
        import apps.agenda.signals  # noqa: F401
