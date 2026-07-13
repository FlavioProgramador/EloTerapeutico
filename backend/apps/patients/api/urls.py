from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.patients.api.serializers.form_serializers import PatientFormSerializer
from apps.patients.api.serializers.legacy_serializers import PatientDetailSerializer
from apps.patients.api.serializers.list_serializers import PatientReferenceListSerializer
from apps.patients.api.views.dashboard_actions import PatientDashboardActions
from apps.patients.api.views.export_actions import PatientExportActions
from apps.patients.api.views.patient_viewset import PatientViewSet
from apps.patients.api.views.reminder_view import PatientReminderView
from apps.patients.selectors.dashboard_queries import annotate_dashboard, annotate_essential
from apps.patients.selectors.patients import patients_accessible_to


class PatientDashboardViewSet(
    PatientDashboardActions,
    PatientExportActions,
    PatientViewSet,
):
    def get_queryset(self):
        requested_statuses = set(self.request.query_params.getlist("status"))
        include_deleted = self.action == "restore" or bool(requested_statuses.intersection({"archived", "inactive"}))
        queryset = patients_accessible_to(
            self.request.user,
            include_deleted=include_deleted,
        )

        # Otimização: Aplicar anotações pesadas apenas quando necessário.
        # As métricas não precisam de nenhuma anotação.
        if self.action == "dashboard_metrics":
            return queryset.order_by("full_name")

        # A listagem e exportação usam apenas anotações essenciais.
        if self.action in ["list", "export_csv"]:
            return annotate_essential(queryset.order_by("full_name"))

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
