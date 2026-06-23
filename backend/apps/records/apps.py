"""
apps/records/apps.py
Configuração do app de Prontuários Eletrônicos (Records).

Este app gerencia:
- Anamnese inicial do paciente
- Evoluções de sessão (com criptografia e travamento automático em 48h)
- Aditivos a evoluções bloqueadas
"""

from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.records"
    verbose_name = "Prontuários"

    def ready(self):
        """
        Importa os signals ao iniciar o app.
        O signal post_save em Evolution é registrado aqui.
        """
        import apps.records.signals  # noqa: F401
