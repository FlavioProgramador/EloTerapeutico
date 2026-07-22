from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scheduling.api.views.base import ScopedAgendaMixin
from apps.scheduling.selectors.resources import telemedicine_rooms_queryset
from apps.scheduling.selectors.telemedicine_metrics import (
    get_telemedicine_operational_metrics,
)


class TelemedicineOperationalMetricsView(ScopedAgendaMixin, APIView):
    """Métricas agregadas do tenant atual, sem dados pessoais ou clínicos."""

    def get(self, request):
        del request
        queryset = self.scope_queryset(
            telemedicine_rooms_queryset(),
            therapist_field="appointment__therapist",
        )
        return Response(get_telemedicine_operational_metrics(queryset))
