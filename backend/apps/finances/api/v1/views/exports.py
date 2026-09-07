"""Endpoint de exportação financeira."""

from django.http import HttpResponse
from rest_framework.decorators import action

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event
from apps.finances.services import transactions_csv


class TransactionExportActionsMixin:
    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        transactions = self.filter_queryset(self.get_queryset())
        content = transactions_csv(transactions)
        record_audit_event(
            action=AuditLog.Action.EXPORT,
            actor=request.user,
            resource_label="financeiro.FinancialTransaction",
            resource_repr=f"Exportação CSV de {len(transactions)} transações financeiras",
            request=request,
            source=f"drf:{self.__class__.__name__}",
            on_commit=False,
        )
        response = HttpResponse(content, content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = (
            'attachment; filename="fluxo-financeiro.csv"'
        )
        return response
