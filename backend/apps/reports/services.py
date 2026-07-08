# mypy: ignore-errors
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Max, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.agenda.models import Appointment, PatientPackage
from apps.financeiro.models import FinancialTransaction, MonthlySubscription
from apps.patients.models import Patient

ZERO = Decimal("0.00")


def decimal_to_number(value: Decimal | int | float | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def safe_int(value: str | None, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def resolve_period(params) -> tuple[date, date]:
    today = timezone.localdate()
    custom_start = parse_iso_date(params.get("start_date"))
    custom_end = parse_iso_date(params.get("end_date"))
    if custom_start and custom_end:
        if custom_start > custom_end:
            raise ValueError("Data inicial maior que a data final.")
        return custom_start, custom_end

    period = params.get("period") or "this_month"
    if period == "today":
        return today, today
    if period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if period == "last_30_days":
        return today - timedelta(days=30), today
    if period == "last_90_days":
        return today - timedelta(days=90), today
    if period == "this_year":
        return date(today.year, 1, 1), today

    start = date(today.year, today.month, 1)
    end = date(today.year, today.month, monthrange(today.year, today.month)[1])
    return start, end


def month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def iter_months(start: date, end: date):
    current = month_start(start)
    limit = month_start(end)
    while current <= limit:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def month_key(value: date | datetime) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return f"{value.year:04d}-{value.month:02d}"


def label_month(value: date | datetime) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%m/%Y")


def page_queryset(queryset, params) -> dict[str, Any]:
    page = safe_int(params.get("page"), 1, 1, 10_000)
    page_size = safe_int(params.get("page_size"), 25, 1, 100)
    total = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    return {"count": total, "page": page, "page_size": page_size, "items": queryset[start:end]}


def appointment_queryset(user, start: date, end: date):
    return (
        Appointment.objects.filter(therapist=user, start_time__date__range=(start, end))
        .select_related("patient", "therapist", "room")
        .prefetch_related("financial_transactions")
    )


def insurance_label(patient: Patient | None) -> str:
    if not patient:
        return "Sem convenio"
    if patient.payer_type == Patient.PayerType.INSURANCE:
        return patient.insurance_name or "Sem convenio"
    return "Particular"


def appointment_status_labels() -> dict[str, str]:
    return dict(Appointment.Status.choices)


def financial_status_labels() -> dict[str, str]:
    return dict(FinancialTransaction.PaymentStatus.choices)


def transaction_type_labels() -> dict[str, str]:
    return dict(FinancialTransaction.TransactionType.choices)


def category_labels() -> dict[str, str]:
    return dict(FinancialTransaction.Category.choices)


def serialize_appointment(appointment: Appointment) -> dict[str, Any]:
    linked_financial = list(appointment.financial_transactions.all())
    amount = linked_financial[0].amount if linked_financial else appointment.session_value
    return {
        "id": appointment.id,
        "date": timezone.localtime(appointment.start_time).date().isoformat(),
        "start_time": timezone.localtime(appointment.start_time).isoformat(),
        "end_time": timezone.localtime(appointment.end_time).isoformat(),
        "patient": appointment.patient.display_name,
        "professional": appointment.therapist.full_name,
        "status": appointment.status,
        "status_display": appointment.get_status_display(),
        "room": appointment.room.name if appointment.room else "Sem sala definida",
        "insurance": insurance_label(appointment.patient),
        "amount": decimal_to_number(amount),
    }


def appointments_report(user, params) -> dict[str, Any]:
    start, end = resolve_period(params)
    queryset = appointment_queryset(user, start, end)

    patient_filter = params.get("patient")
    professional_filter = params.get("professional")
    status_filter = params.get("status")
    insurance_filter = params.get("insurance")
    room_filter = params.get("room")
    if patient_filter and patient_filter != "all":
        queryset = queryset.filter(patient_id=patient_filter)
    if professional_filter and professional_filter != "all":
        queryset = queryset.filter(therapist_id=professional_filter)
    if status_filter and status_filter != "all":
        queryset = queryset.filter(status=status_filter)
    if room_filter and room_filter != "all":
        queryset = queryset.filter(room_id=room_filter)
    if insurance_filter and insurance_filter != "all":
        if insurance_filter == "private":
            queryset = queryset.filter(patient__payer_type=Patient.PayerType.PRIVATE)
        else:
            queryset = queryset.filter(patient__insurance_name=insurance_filter)

    total = queryset.count()
    completed = queryset.filter(status=Appointment.Status.COMPLETED).count()
    cancelled = queryset.filter(status=Appointment.Status.CANCELLED).count()
    missed = queryset.filter(status=Appointment.Status.MISSED).count()
    rate = lambda value: round((value / total) * 100, 1) if total else 0

    status_counts = {item["status"]: item["count"] for item in queryset.values("status").annotate(count=Count("id"))}
    status_distribution = [
        {"label": label, "key": key, "value": status_counts.get(key, 0)}
        for key, label in appointment_status_labels().items()
    ]

    by_room = []
    for item in queryset.values("room__name").annotate(value=Count("id")).order_by("room__name"):
        by_room.append({"label": item["room__name"] or "Sem sala definida", "value": item["value"]})

    insurance_map: dict[str, int] = {}
    for appointment in queryset.select_related("patient"):
        label = insurance_label(appointment.patient)
        insurance_map[label] = insurance_map.get(label, 0) + 1
    by_insurance = [{"label": key, "value": value} for key, value in sorted(insurance_map.items())]

    buckets = [(6, 8), (8, 10), (10, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22)]
    busy_hours = [{"label": f"{start_h:02d}h-{end_h:02d}h", "value": 0} for start_h, end_h in buckets]
    for appointment in queryset:
        hour = timezone.localtime(appointment.start_time).hour
        for index, (start_h, end_h) in enumerate(buckets):
            if start_h <= hour < end_h:
                busy_hours[index]["value"] += 1
                break

    monthly = {
        month_key(month): {
            "month": month_key(month),
            "label": label_month(month),
            "completed": 0,
            "cancelled": 0,
            "missed": 0,
        }
        for month in iter_months(start, end)
    }
    for item in queryset.annotate(month=TruncMonth("start_time")).values("month", "status").annotate(count=Count("id")):
        key = month_key(item["month"])
        if key not in monthly:
            continue
        if item["status"] == Appointment.Status.COMPLETED:
            monthly[key]["completed"] = item["count"]
        elif item["status"] == Appointment.Status.CANCELLED:
            monthly[key]["cancelled"] = item["count"]
        elif item["status"] == Appointment.Status.MISSED:
            monthly[key]["missed"] = item["count"]

    paginated = page_queryset(queryset.order_by("-start_time"), params)
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "kpis": {
            "total": total,
            "attendance_rate": rate(completed),
            "cancellation_rate": rate(cancelled),
            "miss_rate": rate(missed),
        },
        "charts": {
            "status_distribution": status_distribution,
            "by_room": by_room,
            "by_insurance": by_insurance,
            "busy_hours": busy_hours,
            "monthly_evolution": list(monthly.values()),
        },
        "table": {
            "count": paginated["count"],
            "page": paginated["page"],
            "page_size": paginated["page_size"],
            "results": [serialize_appointment(item) for item in paginated["items"]],
        },
    }


def serialize_patient_risk(patient: Patient, threshold: int) -> dict[str, Any]:
    today = timezone.localdate()
    last = patient.last_appointment.date() if getattr(patient, "last_appointment", None) else None
    next_appt = patient.next_appointment.date() if getattr(patient, "next_appointment", None) else None
    days_without = (today - last).days if last else threshold
    return {
        "id": patient.id,
        "patient": patient.display_name,
        "professional": patient.therapist.full_name,
        "last_appointment": last.isoformat() if last else None,
        "next_appointment": next_appt.isoformat() if next_appt else None,
        "days_without_appointment": days_without,
        "status": patient.status,
        "status_display": patient.get_status_display(),
        "contact": patient.whatsapp or patient.phone or patient.email,
    }


def patients_report(user, params) -> dict[str, Any]:
    start, end = resolve_period(params)
    risk_days = safe_int(params.get("risk_days"), 30, 1, 3650)
    today = timezone.localdate()
    cutoff = today - timedelta(days=risk_days)

    patients = Patient.objects.filter(therapist=user).select_related("therapist")
    active = patients.filter(
        is_active=True,
        status__in=[
            Patient.Status.ACTIVE,
            Patient.Status.EVALUATION,
            Patient.Status.WAITING_RETURN,
        ],
    )
    active_total = active.count()
    new_in_period = patients.filter(created_at__date__range=(start, end)).count()
    active_with_appointment = active.filter(appointments__start_time__date__range=(start, end)).distinct().count()
    retention = round((active_with_appointment / active_total) * 100, 1) if active_total else 0

    monthly = {
        month_key(month): {"month": month_key(month), "label": label_month(month), "value": 0}
        for month in iter_months(start, end)
    }
    for item in (
        patients.filter(created_at__date__range=(start, end))
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
    ):
        key = month_key(item["month"])
        if key in monthly:
            monthly[key]["value"] = item["count"]

    inactive_total = patients.exclude(id__in=active.values("id")).count()
    by_professional = [{"label": user.full_name or "Sem profissional", "value": patients.count()}]

    age_buckets = [
        (0, 5, "0-5"),
        (6, 10, "6-10"),
        (11, 17, "11-17"),
        (18, 25, "18-25"),
        (26, 35, "26-35"),
        (36, 45, "36-45"),
        (46, 60, "46-60"),
        (61, 200, "60+"),
    ]
    age_distribution = [{"label": label, "value": 0} for _, _, label in age_buckets]
    age_distribution.append({"label": "Sem data", "value": 0})
    for patient in patients:
        age = patient.age
        if age is None:
            age_distribution[-1]["value"] += 1
            continue
        for index, (minimum, maximum, _label) in enumerate(age_buckets):
            if minimum <= age <= maximum:
                age_distribution[index]["value"] += 1
                break

    risk_query = active.annotate(
        last_appointment=Max("appointments__start_time", filter=Q(appointments__status=Appointment.Status.COMPLETED)),
        next_appointment=Max(
            "appointments__start_time",
            filter=Q(
                appointments__start_time__date__gte=today,
                appointments__status__in=[
                    Appointment.Status.SCHEDULED,
                    Appointment.Status.CONFIRMED,
                ],
            ),
        ),
    ).filter(Q(last_appointment__date__lt=cutoff) | Q(last_appointment__isnull=True))

    status_filter = params.get("status")
    professional_filter = params.get("professional")
    if status_filter and status_filter != "all":
        risk_query = risk_query.filter(status=status_filter)
    if professional_filter and professional_filter != "all":
        risk_query = risk_query.filter(therapist_id=professional_filter)

    paginated = page_queryset(risk_query.order_by("last_appointment", "full_name"), params)
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "kpis": {
            "active_patients": active_total,
            "new_patients": new_in_period,
            "evasion_risk": risk_query.count(),
            "retention_rate": retention,
        },
        "charts": {
            "new_patients_by_month": list(monthly.values()),
            "active_vs_inactive": [
                {"label": "Ativos", "value": active_total},
                {"label": "Inativos", "value": inactive_total},
            ],
            "patients_by_professional": by_professional,
            "age_distribution": age_distribution,
        },
        "risk": {
            "count": paginated["count"],
            "page": paginated["page"],
            "page_size": paginated["page_size"],
            "results": [serialize_patient_risk(item, risk_days) for item in paginated["items"]],
        },
    }


def transaction_queryset(user, start: date, end: date):
    return (
        FinancialTransaction.objects.filter(therapist=user)
        .filter(
            Q(due_date__range=(start, end))
            | Q(paid_at__date__range=(start, end))
            | Q(created_at__date__range=(start, end))
        )
        .select_related("patient")
    )


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
        "paid_at": timezone.localtime(transaction.paid_at).isoformat() if transaction.paid_at else None,
    }


def financial_report(user, params) -> dict[str, Any]:
    start, end = resolve_period(params)
    today = timezone.localdate()
    all_transactions = FinancialTransaction.objects.filter(therapist=user).select_related("patient")
    queryset = transaction_queryset(user, start, end)

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
        F("amount") - F("paid_amount"), output_field=DecimalField(max_digits=12, decimal_places=2)
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

    income_base = queryset.filter(transaction_type=FinancialTransaction.TransactionType.INCOME)
    expense_base = queryset.filter(transaction_type=FinancialTransaction.TransactionType.EXPENSE)
    gross = (
        income_base.exclude(
            payment_status__in=[
                FinancialTransaction.PaymentStatus.CANCELLED,
                FinancialTransaction.PaymentStatus.REFUNDED,
            ]
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    cancellations = (
        income_base.filter(
            payment_status__in=[
                FinancialTransaction.PaymentStatus.CANCELLED,
                FinancialTransaction.PaymentStatus.REFUNDED,
            ]
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    expenses = (
        expense_base.exclude(
            payment_status__in=[
                FinancialTransaction.PaymentStatus.CANCELLED,
                FinancialTransaction.PaymentStatus.REFUNDED,
            ]
        ).aggregate(total=Sum("amount"))["total"]
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
                "patient": item.patient.display_name if item.patient else "Sem paciente",
                "value": ZERO,
                "titles": 0,
                "oldest_due_date": item.due_date,
            }
        overdue_by_patient[key]["value"] += item.outstanding
        overdue_by_patient[key]["titles"] += 1
        if item.due_date and (
            not overdue_by_patient[key]["oldest_due_date"] or item.due_date < overdue_by_patient[key]["oldest_due_date"]
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
    delinquency.sort(key=lambda row: (row["value"], row["days_overdue"]), reverse=True)

    revenue_by_insurance: dict[str, Decimal] = {}
    for item in income_base.exclude(
        payment_status__in=[
            FinancialTransaction.PaymentStatus.CANCELLED,
            FinancialTransaction.PaymentStatus.REFUNDED,
        ]
    ).select_related("patient"):
        label = insurance_label(item.patient)
        revenue_by_insurance[label] = revenue_by_insurance.get(label, ZERO) + item.amount

    active_subscriptions = MonthlySubscription.objects.filter(therapist=user, status=MonthlySubscription.Status.ACTIVE)
    monthly_amount = active_subscriptions.aggregate(total=Sum("monthly_amount"))["total"] or ZERO
    packages = PatientPackage.objects.filter(therapist=user, status=PatientPackage.Status.ACTIVE)
    package_remaining = ZERO
    for package in packages:
        package_remaining += package.unit_value * Decimal(package.remaining_sessions)
    package_monthly_slice = package_remaining / Decimal("3") if package_remaining else ZERO
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
            {"label": key, "value": decimal_to_number(value)} for key, value in sorted(revenue_by_insurance.items())
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
            "results": [serialize_transaction(item) for item in paginated["items"]],
        },
    }


def online_scheduling_report(user, params) -> dict[str, Any]:
    start, end = resolve_period(params)
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "enabled": False,
        "kpis": {
            "views": 0,
            "unique_views": 0,
            "requests": 0,
            "pending_requests": 0,
            "conversion_rate": 0,
            "average_approval_minutes": 0,
        },
        "statuses": {
            "approved": {"count": 0, "percentage": 0},
            "pending": {"count": 0, "percentage": 0},
            "rejected": {"count": 0, "percentage": 0},
        },
    }
