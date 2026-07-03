from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .dashboard_actions import PatientDashboardActions
from .dashboard_queries import annotate_dashboard
from .export_actions import PatientExportActions
from .form_serializers import PatientFormSerializer
from .list_serializers import PatientReferenceListSerializer
from .models import Patient
from .patient_viewset import PatientViewSet
from .reminder_view import PatientReminderView
from .serializers import PatientDetailSerializer


class PatientDashboardViewSet(
    PatientDashboardActions,
    PatientExportActions,
    PatientViewSet,
):
    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Patient.objects.none()

        requested_statuses = set(self.request.query_params.getlist("status"))
        include_deleted = self.action == "restore" or bool(
            requested_statuses.intersection({"archived", "inactive"})
        )
        manager = Patient.all_objects if include_deleted else Patient.objects
        if user.is_admin_role or user.is_secretary:
            queryset = manager.all()
        else:
            queryset = manager.filter(therapist=user)
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
    path(
        "<int:pk>/reminders/",
        PatientReminderView.as_view(),
        name="patient-reminders",
    ),
    path("", include(router.urls)),
]
