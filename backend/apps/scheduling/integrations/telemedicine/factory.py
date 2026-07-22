from __future__ import annotations

from django.conf import settings

from .base import TelemedicineProvider
from .exceptions import TelemedicineProviderConfigurationError
from .fake import FakeTelemedicineProvider
from .livekit import LiveKitTelemedicineProvider


def get_telemedicine_provider() -> TelemedicineProvider:
    provider_name = getattr(settings, "TELEMEDICINE_PROVIDER", "livekit").lower()
    if provider_name == "livekit":
        return LiveKitTelemedicineProvider()
    if provider_name == "fake" and settings.DEBUG:
        return FakeTelemedicineProvider()
    raise TelemedicineProviderConfigurationError(
        "O provedor de atendimento online não está disponível."
    )
