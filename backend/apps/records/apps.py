from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.records"
    verbose_name = "Prontuários"

    def ready(self):
        import apps.records.models.templates  # noqa: F401
        import apps.records.signals  # noqa: F401
