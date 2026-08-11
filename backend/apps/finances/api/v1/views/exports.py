"""Endpoint de exportação financeira."""

from django.http import HttpResponse
from rest_framework.decorators import action

from apps.finances.services import transactions_csv


class TransactionExportActionsMixin:
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        content = transactions_csv(self.filter_queryset(self.get_queryset()))
        response = HttpResponse(content, content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = (
            'attachment; filename="fluxo-financeiro.csv"'
        )
        return response
