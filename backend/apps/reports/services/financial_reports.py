# mypy: ignore-errors
"""Construção do relatório financeiro."""

from datetime import date
from decimal import Decimal
from typing import Any

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.reports.selectors import (
    active_packages_for_user,
    active_subscriptions_for_user,
    all_transactions_for_user,
    transactions_for_period,
)
from apps.reports.services.periods import (
    label_month,
    month_key,
    page_queryset,
    resolve_period,
)
from apps.reports.services.tenant import resolve_report_organization
from apps.reports.services.value_formatting import decimal_to_number, insurance_label

ZERO = Decimal("0.00")


def serialize_transaction(transaction: FinancialTransaction) -> dict[str, Any]:
    return {
        "id": transaction.id,
        "date": transaction.created_at.date().isoformat(),
        "type": transaction.transaction_type,
        "type_display": transaction.get_transaction_type_display(),
        "description": transaction.description or transaction.get_category_display(),
        "patient": transaction.patient.display_name if transaction.patient else "-",
        "category": transaction.category,
        "category_display": transaction.get_category_display(),
        "insurance": insurance_label(transaction.patient) if transaction.patient else "-",
        "amount": decimal_to_number(transaction.amount),
        "paid_amount": decimal_to_number(transaction.paid_amount),
        "outstanding_amount": decimal_to_number(transaction.outstanding_amount),
        "status": transaction.payment_status,
        "status_display": transaction.get_payment_status_display(),
        "due_date": transaction.due_date.isoformat() if transaction.due_date else None,
        "paid_at": (
            timezone.localtime(transaction.paid_at).isoformat()
            if transaction.paid_at
            else None
        ),
    }


def financial_report(user, params, organization=None) -> dict[str, Any]:
    start, end = resolve_period(params)
    organization = resolve_report_organization(user=user, organization=organization)
    today = timezone.localdate()
    all_transactions = all_transactions_for_user(
        user=user,
        organization=organization,
    )
    queryset = transactions_for_period(
        user=user,
        organization=organization,
        start=start,
        end=end,
    )

    type_filter = params.get("transaction_type") or params.get("type")
    status_filter = params.get("status")
    patient_filter = params.get("patient")
    category_filter = params.get("category")
    insurance_filter = params.get("insurance")
    if type_filter and type_filter != "all":
        queryset = queryset.filter(transaction_type=type_filter)
    if status_filter and status_filter != "all":
        queryset = queryset.filter(payment_status=status_filter)
    if patient_filter and patient_filter != "all":
        queryset = queryset.filter(patient_id=patient_filter)
    if category_filter and category_filter != "all":
        queryset = queryset.filter(category=category_filter)
    if insurance_filter and insurance_filter != "all":
        if insurance_filter == "private":
            queryset = queryset.filter(patient__payer_type=Patient.PayerType.PRIVATE)
        else:
            queryset = queryset.filter(patient__insurance_name=insurance_filter)

    outstanding_expr = ExpressionWrapper(
        F("amount") - F("paid_amount"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
    overdue = all_transactions.filter(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ],
        due_date__lt=today,
    ).annotate(outstanding=outstanding_expr)
    overdue_value = overdue.aggregate(total=Sum("outstanding"))["total"] or ZERO

    income_base = queryset.filter(
        transaction_type=FinancialTransaction.TransactionType.INCOME
    )
    expense_base = queryset.filter(
        transaction_type=FinancialTransaction.TransactionType.EXPENSE
    )
    excluded_statuses = [
        FinancialTransaction.PaymentStatus.CANCELLED,
        FinancialTransaction.PaymentStatus.REFUNDED,
    ]
    gross = (
        income_base.exclude(payment_status__in=excluded_statuses).aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )
    cancellations = (
        income_base.filter(payment_status__in=excluded_statuses).aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )
    expenses = (
        expense_base.exclude(payment_status__in=excluded_statuses).aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )
    net_revenue = gross - cancellations
    operational_result = net_revenue - expenses

    delinquency = []
    overdue_by_patient: dict[int, dict[str, Any]] = {}
    for item in overdue.select_related("patient"):
        key = item.patient_id or 0
        if key not in overdue_by_patient:
            overdue_by_patient[key] = {
                "patient": (
                    item.patient.display_name if item.patient else "Sem paciente"
                ),
                "value": ZERO,
                "titles": 0,
                "oldest_due_date": item.due_date,
            }
        overdue_by_patient[key]["value"] += item.outstanding
        overdue_by_patient[key]["titles"] += 1
        if item.due_date and (
            not overdue_by_patient[key]["oldest_due_date"]
            or item.due_date < overdue_by_patient[key]["oldest_due_date"]
        ):
            overdue_by_patient[key]["oldest_due_date"] = item.due_date
    for item in overdue_by_patient.values():
        oldest = item["oldest_due_date"]
        delinquency.append(
            {
                "patient": item["patient"],
                "value": decimal_to_number(item["value"]),
                "titles": item["titles"],
                "days_overdue": (today - oldest).days if oldest else 0,
            }
        )
    delinquency.sort(
        key=lambda row: (row["value"], row["days_overdue"]),
        reverse=True,
    )

    revenue_by_insurance: dict[str, Decimal] = {}
    for item in income_base.exclude(
        payment_status__in=excluded_statuses
    ).select_related("patient"):
        label = insurance_label(item.patient)
        revenue_by_insurance[label] = (
            revenue_by_insurance.get(label, ZERO) + item.amount
        )

    active_subscriptions = active_subscriptions_for_user(
        user=user,
        organization=organization,
    )
    monthly_amount = (
        active_subscriptions.aggregate(total=Sum("monthly_amount"))["total"]
        or ZERO
    )
    packages = active_packages_for_user(user=user, organization=organization)
    package_remaining = ZERO
    for package in packages:
        package_remaining += package.unit_value * Decimal(package.remaining_sessions)
    package_monthly_slice = (
        package_remaining / Decimal("3") if package_remaining else ZERO
    )
    projection_series = []
    for offset in range(3):
        month = date(
            today.year + ((today.month + offset - 1) // 12),
            ((today.month + offset - 1) % 12) + 1,
            1,
        )
        projection_series.append(
            {
                "month": month_key(month),
                "label": label_month(month),
                "value": decimal_to_number(monthly_amount + package_monthly_slice),
            }
        )
    projected_total = (monthly_amount * Decimal("3")) + package_remaining

    paginated = page_queryset(queryset.order_by("-created_at"), params)
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "kpis": {
            "overdue_titles": overdue.count(),
            "overdue_value": decimal_to_number(overdue_value),
            "operational_result": decimal_to_number(operational_result),
            "projected_revenue_3m": decimal_to_number(projected_total),
        },
        "delinquency_by_patient": delinquency,
        "revenue_by_insurance": [
            {"label": key, "value": decimal_to_number(value)}
            for key, value in sorted(revenue_by_insurance.items())
        ],
        "dre": {
            "gross_revenue": decimal_to_number(gross),
            "cancellations": decimal_to_number(cancellations),
            "net_revenue": decimal_to_number(net_revenue),
            "expenses": decimal_to_number(expenses),
            "operational_result": decimal_to_number(operational_result),
        },
        "projection": {
            "monthly_active": decimal_to_number(monthly_amount),
            "package_remaining": decimal_to_number(package_remaining),
            "projected_total_3m": decimal_to_number(projected_total),
            "series": projection_series,
        },
        "transactions": {
            "count": paginated["count"],
            "page": paginated["page"],
            "page_size": paginated["page_size"],
            "results": [
                serialize_transaction(item) for item in paginated["items"]
            ],
        },
    }
