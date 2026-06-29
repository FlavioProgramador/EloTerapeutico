"""Configuração do app de Prontuários Eletrônicos."""

from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.records"
    verbose_name = "Prontuários"

    def ready(self):
        """Registra sinais e modelos complementares do domínio clínico."""
        import apps.records.extended_models  # noqa: F401
        import apps.records.signals  # noqa: F401
        import apps.records.treatment_models  # noqa: F401
