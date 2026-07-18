"""Views de telemedicina."""

from apps.scheduling.api.views.telemedicine import (
    TelemedicineAccessView,
    TelemedicineRoomViewSet,
)

__all__ = ["TelemedicineAccessView", "TelemedicineRoomViewSet"]
