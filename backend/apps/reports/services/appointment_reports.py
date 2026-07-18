# mypy: ignore-errors
"""Construção do relatório de consultas."""

from typing import Any

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.patients.models import Patient
from apps.reports.selectors import appointments_for_period
from apps.reports.services.periods import iter_months, label_month, month_key, page_queryset, resolve_period
from apps.reports.services.value_formatting import decimal_to_number, insurance_label
from apps.scheduling.models import Appointment


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
    queryset = appointments_for_period(owner=user, start=start, end=end)

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
        for key, label in Appointment.Status.choices
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
