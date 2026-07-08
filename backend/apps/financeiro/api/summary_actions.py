"""Indicadores do painel financeiro."""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import FinancialTransaction


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
            Q(due_date__range=(start_date, end_date))
            | Q(paid_at__date__range=(start_date, end_date))
        ).exclude(payment_status__in=["cancelled", "refunded"])

        metrics = queryset.aggregate(
            received=Sum(
                "amount",
                filter=Q(
                    transaction_type="income",
                    payment_status="paid",
                    paid_at__date__range=(start_date, end_date),
                ),
            ),
            received_count=Count(
                "id",
                filter=Q(
                    transaction_type="income",
                    payment_status="paid",
                    paid_at__date__range=(start_date, end_date),
                ),
            ),
            paid_expenses=Sum(
                "amount",
                filter=Q(
                    transaction_type="expense",
                    payment_status="paid",
                    paid_at__date__range=(start_date, end_date),
                ),
            ),
            paid_expenses_count=Count(
                "id",
                filter=Q(
                    transaction_type="expense",
                    payment_status="paid",
                    paid_at__date__range=(start_date, end_date),
                ),
            ),
            receivable_total=Sum(
                "amount",
                filter=Q(
                    transaction_type="income",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            receivable_paid=Sum(
                "paid_amount",
                filter=Q(
                    transaction_type="income",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            receivable_count=Count(
                "id",
                filter=Q(
                    transaction_type="income",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            payable_total=Sum(
                "amount",
                filter=Q(
                    transaction_type="expense",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            payable_paid=Sum(
                "paid_amount",
                filter=Q(
                    transaction_type="expense",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            payable_count=Count(
                "id",
                filter=Q(
                    transaction_type="expense",
                    payment_status__in=["pending", "partial"],
                    due_date__range=(start_date, end_date),
                ),
            ),
            overdue_total=Sum(
                "amount",
                filter=Q(
                    payment_status__in=["pending", "partial"],
                    due_date__lt=today,
                ),
            ),
            overdue_paid=Sum(
                "paid_amount",
                filter=Q(
                    payment_status__in=["pending", "partial"],
                    due_date__lt=today,
                ),
            ),
            overdue_receivable_count=Count(
                "id",
                filter=Q(
                    transaction_type="income",
                    payment_status__in=["pending", "partial"],
                    due_date__lt=today,
                ),
            ),
            overdue_payable_count=Count(
                "id",
                filter=Q(
                    transaction_type="expense",
                    payment_status__in=["pending", "partial"],
                    due_date__lt=today,
                ),
            ),
            transaction_count=Count("id"),
        )

        received = metrics["received"] or Decimal("0.00")
        paid_expenses = metrics["paid_expenses"] or Decimal("0.00")
        receivable = (metrics["receivable_total"] or Decimal("0.00")) - (
            metrics["receivable_paid"] or Decimal("0.00")
        )
        payable = (metrics["payable_total"] or Decimal("0.00")) - (
            metrics["payable_paid"] or Decimal("0.00")
        )
        overdue = (metrics["overdue_total"] or Decimal("0.00")) - (
            metrics["overdue_paid"] or Decimal("0.00")
        )

        return Response(
            {
                "start_date": start_date,
                "end_date": end_date,
                "received": received,
                "received_count": metrics["received_count"],
                "receivable": receivable,
                "receivable_count": metrics["receivable_count"],
                "payable": payable,
                "payable_count": metrics["payable_count"],
                "paid_expenses": paid_expenses,
                "paid_expenses_count": metrics["paid_expenses_count"],
                "overdue": overdue,
                "overdue_receivable_count": metrics["overdue_receivable_count"],
                "overdue_payable_count": metrics["overdue_payable_count"],
                "projected_balance": received + receivable - paid_expenses - payable,
                "transaction_count": metrics["transaction_count"],
                "total_income": received,
                "total_expense": paid_expenses,
                "balance": received - paid_expenses,
                "total_pending": receivable + payable,
            }
        )
