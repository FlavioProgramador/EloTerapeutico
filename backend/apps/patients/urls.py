from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .dashboard_actions import PatientDashboardActions
from .dashboard_queries import annotate_dashboard
from .dashboard_serializers import PatientDashboardSerializer
from .export_actions import PatientExportActions
from .form_serializers import PatientFormSerializer
from .serializers import PatientDetailSerializer
from .views import PatientViewSet


class PatientDashboardViewSet(
    PatientDashboardActions,
    PatientExportActions,
    PatientViewSet,
):
    def get_queryset(self):
        return annotate_dashboard(super().get_queryset())

    def get_serializer_class(self):
        if self.action == "list":
            return PatientDashboardSerializer
        if self.action in ["create", "update", "partial_update"]:
            return PatientFormSerializer
        return PatientDetailSerializer


router = DefaultRouter()
router.register(r"", PatientDashboardViewSet, basename="patient")

urlpatterns = [path("", include(router.urls))]
