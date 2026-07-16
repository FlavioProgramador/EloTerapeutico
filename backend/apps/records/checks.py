"""System checks de segurança do prontuário."""

import os

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register

from apps.records.services.malware_scanning import clamav_host, scanner_backend, scanner_mock_allowed


def _settings_module() -> str:
    explicit = str(getattr(settings, "SETTINGS_MODULE", "") or "").strip()
    return explicit or os.getenv("DJANGO_SETTINGS_MODULE", "").strip()


@register(Tags.security)
def clinical_upload_scanner_check(app_configs, **kwargs):
    """Impede que produção aceite uploads sem análise antimalware."""

    del app_configs, kwargs
    if _settings_module().endswith(".test"):
        return []

    backend = scanner_backend()
    if backend.startswith("mock_"):
        if scanner_mock_allowed() and settings.DEBUG:
            return [
                Warning(
                    "Scanner clínico mock está ativo em desenvolvimento.",
                    id="records.W002",
                )
            ]
        return [
            Error(
                "Scanner clínico mock não pode ser usado neste ambiente.",
                id="records.E002",
            )
        ]

    if settings.DEBUG:
        if backend != "clamd":
            return [
                Warning(
                    "Uploads clínicos permanecerão em quarentena até configurar ClamAV.",
                    hint="Configure CLINICAL_UPLOAD_SCANNER_BACKEND=clamd e CLAMAV_HOST.",
                    id="records.W001",
                )
            ]
        if not clamav_host():
            return [
                Warning(
                    "CLAMAV_HOST não está configurado; uploads permanecerão em quarentena.",
                    id="records.W003",
                )
            ]
        return []

    errors = []
    if backend != "clamd":
        errors.append(
            Error(
                "Produção exige CLINICAL_UPLOAD_SCANNER_BACKEND=clamd.",
                id="records.E001",
            )
        )
    if backend == "clamd" and not clamav_host():
        errors.append(
            Error(
                "Produção exige CLAMAV_HOST configurado.",
                id="records.E003",
            )
        )
    return errors
