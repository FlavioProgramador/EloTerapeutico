"""
apps/patients/apps.py
Configuração do aplicativo Pacientes.
"""

from django.apps import AppConfig


class PatientsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.patients"
    verbose_name = "Pacientes"

    def ready(self):
        """
        Importa os signals do app ao inicializar.
        Placeholder para futuras implementações de signals.
        """
        pass
