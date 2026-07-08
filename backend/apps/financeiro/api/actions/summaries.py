"""Actions de indicadores do painel financeiro."""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response


def _total(queryset, field="amount"):
    return queryset.aggregate(value=Sum(field))["value"] or Decimal("0.00")


class FinancialSummaryActions:
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        today = timezone.localdate()
        try:
            if request.query_params.get("start_date") and request.query_params.get("end_date"):
                start_date = date.fromisoformat(request.query_params["start_date"])
                end_date = date.fromisoformat(request.query_params["end_date"])
            else:
                year = int(request.query_params.get("year") or today.year)
                month = int(request.query_params.get("month") or today.month)
                start_date = date(year, month, 1)
                end_date = date(year, month, monthrange(year, month)[1])
            if start_date > end_date:
                raise ValueError
        except (TypeError, ValueError):
            return Response({"detail": "Informe um período válido."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(
            Q(due_date__range=(start_date, end_date)) | Q(paid_at__date__range=(start_date, end_date))
        ).exclude(payment_status__in=["cancelled", "refunded"])
        opened = queryset.filter(payment_status__in=["pending", "partial"])
        paid = queryset.filter(payment_status="paid")
        received_qs = paid.filter(transaction_type="income", paid_at__date__range=(start_date, end_date))
        paid_expenses_qs = paid.filter(transaction_type="expense", paid_at__date__range=(start_date, end_date))
        receivable_qs = opened.filter(transaction_type="income", due_date__range=(start_date, end_date))
        payable_qs = opened.filter(transaction_type="expense", due_date__range=(start_date, end_date))
        overdue_qs = opened.filter(due_date__lt=today)

        received = _total(received_qs)
        paid_expenses = _total(paid_expenses_qs)
        receivable = _total(receivable_qs) - _total(receivable_qs, "paid_amount")
        payable = _total(payable_qs) - _total(payable_qs, "paid_amount")
        overdue = _total(overdue_qs) - _total(overdue_qs, "paid_amount")

        return Response(
            {
                "start_date": start_date,
                "end_date": end_date,
                "received": received,
                "received_count": received_qs.count(),
                "receivable": receivable,
                "receivable_count": receivable_qs.count(),
                "payable": payable,
                "payable_count": payable_qs.count(),
                "paid_expenses": paid_expenses,
                "paid_expenses_count": paid_expenses_qs.count(),
                "overdue": overdue,
                "overdue_receivable_count": overdue_qs.filter(transaction_type="income").count(),
                "overdue_payable_count": overdue_qs.filter(transaction_type="expense").count(),
                "projected_balance": received + receivable - paid_expenses - payable,
                "transaction_count": queryset.count(),
                "total_income": received,
                "total_expense": paid_expenses,
                "balance": received - paid_expenses,
                "total_pending": receivable + payable,
            }
        )
