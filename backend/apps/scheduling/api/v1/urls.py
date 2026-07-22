"""Rotas REST v1 do domínio de scheduling."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentRecurrenceViewSet,
    AppointmentReminderViewSet,
    AppointmentViewSet,
    LiveKitWebhookView,
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
    TelemedicineAccessView,
    TelemedicinePublicConsentView,
    TelemedicinePublicExchangeView,
    TelemedicinePublicJoinView,
    TelemedicinePublicLeaveView,
    TelemedicineRoomViewSet,
)

router = DefaultRouter()
router.register(r"appointments", AppointmentViewSet, basename="appointment")
router.register(
    r"appointment-recurrences",
    AppointmentRecurrenceViewSet,
    basename="appointment-recurrence",
)
router.register(r"schedule-blocks", ScheduleBlockViewSet, basename="schedule-block")
router.register(r"rooms", RoomViewSet, basename="agenda-room")
router.register(r"patient-packages", PatientPackageViewSet, basename="patient-package")
router.register(r"package-sessions", PackageSessionViewSet, basename="package-session")
router.register(r"telemedicine", TelemedicineRoomViewSet, basename="telemedicine")
router.register(r"reminders", AppointmentReminderViewSet, basename="appointment-reminder")

urlpatterns = [
    path(
        "telemedicine/public/exchange/",
        TelemedicinePublicExchangeView.as_view(),
        name="telemedicine-public-exchange",
    ),
    path(
        "telemedicine/public/consent/",
        TelemedicinePublicConsentView.as_view(),
        name="telemedicine-public-consent",
    ),
    path(
        "telemedicine/public/join/",
        TelemedicinePublicJoinView.as_view(),
        name="telemedicine-public-join",
    ),
    path(
        "telemedicine/public/leave/",
        TelemedicinePublicLeaveView.as_view(),
        name="telemedicine-public-leave",
    ),
    path(
        "integrations/livekit/webhook/",
        LiveKitWebhookView.as_view(),
        name="livekit-webhook",
    ),
    path(
        "telemedicine-access/<str:role>/<uuid:token>/",
        TelemedicineAccessView.as_view(),
        name="telemedicine-access",
    ),
    path("", include(router.urls)),
]
