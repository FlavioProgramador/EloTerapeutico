"""System checks do app Billing."""

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register

_ALLOWED_ASAAS_URLS = {
    "https://api-sandbox.asaas.com/v3",
    "https://api.asaas.com/v3",
}


@register(Tags.security, deploy=True)
def check_asaas_configuration(app_configs, **kwargs):
    if not getattr(settings, "BILLING_ENABLED", True):
        return []

    issues = []
    missing = [
        name
        for name in ("ASAAS_API_KEY", "ASAAS_BASE_URL", "ASAAS_WEBHOOK_TOKEN")
        if not str(getattr(settings, name, "") or "").strip()
    ]
    issue_class = Warning if settings.DEBUG else Error
    if missing:
        issues.append(
            issue_class(
                "Configuração obrigatória do Asaas ausente.",
                hint=f"Configure: {', '.join(missing)}.",
                id="billing.W001" if settings.DEBUG else "billing.E001",
            )
        )

    base_url = str(getattr(settings, "ASAAS_BASE_URL", "") or "").rstrip("/")
    if base_url and base_url not in _ALLOWED_ASAAS_URLS:
        issues.append(
            issue_class(
                "ASAAS_BASE_URL não corresponde a um endpoint oficial suportado.",
                hint=(
                    "Use https://api-sandbox.asaas.com/v3 ou "
                    "https://api.asaas.com/v3."
                ),
                id="billing.W002" if settings.DEBUG else "billing.E002",
            )
        )
    return issues


__all__ = ["check_asaas_configuration"]
