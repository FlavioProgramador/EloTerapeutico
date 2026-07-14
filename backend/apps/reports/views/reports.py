"""Views HTTP dos relatórios analíticos."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.services import (
    appointments_report,
    financial_report,
    online_scheduling_report,
    patients_report,
)

INVALID_PERIOD_RESPONSE = {"detail": "Periodo invalido. Confira a data inicial e a data final informadas."}


class BaseReportView(APIView):
    permission_classes = [IsAuthenticated]

    def build_response(self, request, builder):
        try:
            return Response(builder(request.user, request.query_params))
        except ValueError:
            return Response(INVALID_PERIOD_RESPONSE, status=status.HTTP_400_BAD_REQUEST)


class AppointmentsReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, appointments_report)


class PatientsReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, patients_report)


class FinancialReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, financial_report)


class OnlineSchedulingReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, online_scheduling_report)
