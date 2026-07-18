"""Rotas REST do módulo de Agenda."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.legacy_views import (
    AppointmentRecurrenceViewSet,
    AppointmentReminderViewSet,
    AppointmentViewSet,
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
    TelemedicineAccessView,
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
        "telemedicine-access/<str:role>/<uuid:token>/",
        TelemedicineAccessView.as_view(),
        name="telemedicine-access",
    ),
    path("", include(router.urls)),
]
