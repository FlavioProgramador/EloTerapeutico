"""
apps/financeiro/apps.py
Configuração do app de gestão financeira do Elo Terapêutico.
"""

from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.financeiro"
    verbose_name = "Financeiro"

    def ready(self):
        """Importa signals quando o app estiver pronto (reservado para uso futuro)."""
        pass
