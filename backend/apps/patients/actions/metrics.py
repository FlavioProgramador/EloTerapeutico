"""Action HTTP das métricas agregadas de pacientes."""

from rest_framework.decorators import action
from rest_framework.response import Response

from ..selectors.dashboard import patient_metrics


class PatientMetricsActions:
    @action(detail=False, methods=["get"], url_path="dashboard-metrics")
    def dashboard_metrics(self, request):
        return Response(patient_metrics(self.get_queryset()))
