from django.conf import settings
from django.core.checks import Error, Warning, register

from apps.scheduling.telemedicine_config import get_telemedicine_config


@register()
def check_telemedicine_configuration(app_configs, **kwargs):
    del app_configs, kwargs
    config = get_telemedicine_config()
    issues = []

    if config.enabled and not config.provider_configured:
        issues.append(
            Error(
                "A telemedicina está habilitada sem um provedor válido.",
                hint=(
                    "Defina um provedor suportado e as credenciais correspondentes "
                    "antes de liberar atendimentos online."
                ),
                id="agenda.E001",
            )
        )

    if config.provider == "fake" and not settings.DEBUG:
        issues.append(
            Error(
                "O provider fake de telemedicina não pode ser usado fora do modo DEBUG.",
                id="agenda.E002",
            )
        )

    if config.max_participants != 2:
        issues.append(
            Warning(
                "O MVP de telemedicina foi projetado para exatamente dois participantes.",
                hint="Mantenha TELEMEDICINE_MAX_PARTICIPANTS=2.",
                id="agenda.W001",
            )
        )

    return issues
