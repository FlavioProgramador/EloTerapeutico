from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .dashboard_actions import PatientDashboardActions
from .dashboard_queries import annotate_dashboard
from .export_actions import PatientExportActions
from .form_serializers import PatientFormSerializer
from .list_serializers import PatientReferenceListSerializer
from .models import Patient
from .reminder_view import PatientReminderView
from .serializers import PatientDetailSerializer
from .views import PatientViewSet


class PatientDashboardViewSet(
    PatientDashboardActions,
    PatientExportActions,
    PatientViewSet,
):
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Patient.objects.none()
        include_archived = (
            self.action == "restore"
            or "archived" in self.request.query_params.getlist("status")
        )
        manager = Patient.all_objects if include_archived else Patient.objects
        queryset = manager.all() if user.is_admin_role or user.is_secretary else manager.filter(therapist=user)
        return annotate_dashboard(queryset.order_by("full_name"))

    def get_serializer_class(self):
        if self.action == "list":
            return PatientReferenceListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PatientFormSerializer
        return PatientDetailSerializer


router = DefaultRouter()
router.register(r"", PatientDashboardViewSet, basename="patient")

urlpatterns = [
    path("<int:pk>/reminders/", PatientReminderView.as_view(), name="patient-reminders"),
    path("", include(router.urls)),
]
