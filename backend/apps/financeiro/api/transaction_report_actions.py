"""Resumo mensal e exportação do módulo financeiro."""

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..selectors.transactions import monthly_summary
from ..services.exports import transactions_csv
from .serializers import MonthlySummarySerializer


class TransactionReportActions:
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        today = timezone.localdate()
        try:
            year = int(request.query_params.get("year") or today.year)
            month = int(request.query_params.get("month") or today.month)
            if not 1 <= month <= 12:
                raise ValueError
        except ValueError:
            return Response(
                {"detail": "Ano e mês devem ser inteiros válidos, com mês de 1 a 12."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        therapist = request.user
        therapist_id = request.query_params.get("therapist_id")
        if (request.user.is_admin_role or request.user.is_secretary) and therapist_id:
            therapist = get_object_or_404(
                get_user_model(),
                id=therapist_id,
                role="therapist",
            )
        data = monthly_summary(therapist=therapist, year=year, month=month)
        return Response(MonthlySummarySerializer(data).data)

    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        content = transactions_csv(self.filter_queryset(self.get_queryset()))
        response = HttpResponse(content, content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = (
            'attachment; filename="fluxo-financeiro.csv"'
        )
        return response
