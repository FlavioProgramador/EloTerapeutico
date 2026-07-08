"""Actions de indicadores do painel financeiro."""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

MONEY_FIELD = DecimalField(max_digits=12, decimal_places=2)
ZERO_MONEY = Value(Decimal("0.00"), output_field=MONEY_FIELD)


def _sum(field_name: str, query_filter: Q):
    return Coalesce(
        Sum(field_name, filter=query_filter),
        ZERO_MONEY,
        output_field=MONEY_FIELD,
    )


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
            return Response(
                {"detail": "Informe um período válido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        period_filter = Q(due_date__range=(start_date, end_date)) | Q(
            paid_at__date__range=(start_date, end_date)
        )
        queryset = self.get_queryset().filter(period_filter).exclude(
            payment_status__in=["cancelled", "refunded"]
        )

        open_filter = Q(payment_status__in=["pending", "partial"])
        paid_filter = Q(payment_status="paid")
        received_filter = paid_filter & Q(
            transaction_type="income",
            paid_at__date__range=(start_date, end_date),
        )
        paid_expenses_filter = paid_filter & Q(
            transaction_type="expense",
            paid_at__date__range=(start_date, end_date),
        )
        receivable_filter = open_filter & Q(
            transaction_type="income",
            due_date__range=(start_date, end_date),
        )
        payable_filter = open_filter & Q(
            transaction_type="expense",
            due_date__range=(start_date, end_date),
        )
        overdue_filter = open_filter & Q(due_date__lt=today)
        overdue_receivable_filter = overdue_filter & Q(transaction_type="income")
        overdue_payable_filter = overdue_filter & Q(transaction_type="expense")

        summary = queryset.aggregate(
            received=_sum("amount", received_filter),
            received_count=Count("id", filter=received_filter),
            paid_expenses=_sum("amount", paid_expenses_filter),
            paid_expenses_count=Count("id", filter=paid_expenses_filter),
            receivable_amount=_sum("amount", receivable_filter),
            receivable_paid=_sum("paid_amount", receivable_filter),
            receivable_count=Count("id", filter=receivable_filter),
            payable_amount=_sum("amount", payable_filter),
            payable_paid=_sum("paid_amount", payable_filter),
            payable_count=Count("id", filter=payable_filter),
            overdue_amount=_sum("amount", overdue_filter),
            overdue_paid=_sum("paid_amount", overdue_filter),
            overdue_receivable_count=Count("id", filter=overdue_receivable_filter),
            overdue_payable_count=Count("id", filter=overdue_payable_filter),
            transaction_count=Count("id"),
        )

        received = summary["received"]
        paid_expenses = summary["paid_expenses"]
        receivable = summary["receivable_amount"] - summary["receivable_paid"]
        payable = summary["payable_amount"] - summary["payable_paid"]
        overdue = summary["overdue_amount"] - summary["overdue_paid"]

        return Response(
            {
                "start_date": start_date,
                "end_date": end_date,
                "received": received,
                "received_count": summary["received_count"],
                "receivable": receivable,
                "receivable_count": summary["receivable_count"],
                "payable": payable,
                "payable_count": summary["payable_count"],
                "paid_expenses": paid_expenses,
                "paid_expenses_count": summary["paid_expenses_count"],
                "overdue": overdue,
                "overdue_receivable_count": summary["overdue_receivable_count"],
                "overdue_payable_count": summary["overdue_payable_count"],
                "projected_balance": received + receivable - paid_expenses - payable,
                "transaction_count": summary["transaction_count"],
                "total_income": received,
                "total_expense": paid_expenses,
                "balance": received - paid_expenses,
                "total_pending": receivable + payable,
            }
        )
