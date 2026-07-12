from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing e Assinaturas"

    def ready(self):
        # Registra validações de configuração sem executar chamadas externas no startup.
        from apps.billing import checks  # noqa: F401
