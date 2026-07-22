from __future__ import annotations

from django.conf import settings

from apps.scheduling.telemedicine_config import get_telemedicine_config

from .base import TelemedicineProvider
from .exceptions import TelemedicineProviderConfigurationError
from .fake import FakeTelemedicineProvider
from .livekit import LiveKitTelemedicineProvider


def get_telemedicine_provider() -> TelemedicineProvider:
    provider_name = get_telemedicine_config().provider
    if provider_name == "livekit":
        return LiveKitTelemedicineProvider()
    if provider_name == "fake" and settings.DEBUG:
        return FakeTelemedicineProvider()
    raise TelemedicineProviderConfigurationError(
        "O provedor de atendimento online não está disponível."
    )
