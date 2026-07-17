from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CommunicationAutomationViewSet,
    CommunicationChannelViewSet,
    CommunicationDashboardView,
    CommunicationPreferenceListView,
    CommunicationTemplateViewSet,
    CommunicationViewSet,
    CommunicationWebhookView,
    InAppNotificationViewSet,
    NotificationPreferenceView,
    PatientCommunicationPreferenceView,
)

router = DefaultRouter()
router.register("templates", CommunicationTemplateViewSet, basename="communication-template")
router.register("automations", CommunicationAutomationViewSet, basename="communication-automation")
router.register("notifications", InAppNotificationViewSet, basename="communication-notification")
router.register("channels", CommunicationChannelViewSet, basename="communication-channel")
router.register("", CommunicationViewSet, basename="communication")

urlpatterns = [
    path("webhooks/<str:provider>/", CommunicationWebhookView.as_view(), name="communications-webhook"),
    path("dashboard/", CommunicationDashboardView.as_view(), name="communications-dashboard"),
    path("preferences/", CommunicationPreferenceListView.as_view(), name="communications-preferences"),
    path("notifications/preferences/", NotificationPreferenceView.as_view(), name="notification-preferences"),
    path("preferences/patient/<int:patient_id>/", PatientCommunicationPreferenceView.as_view(), name="communications-patient-preference"),
    path("", include(router.urls)),
]
