from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.records"
    verbose_name = "Prontuários"

    def ready(self):
        import apps.records.evolution_flow_models  # noqa: F401
        import apps.records.extended_models  # noqa: F401
        import apps.records.signals  # noqa: F401
        import apps.records.treatment_models  # noqa: F401
