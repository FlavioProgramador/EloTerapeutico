# mypy: ignore-errors
"""Construção do relatório de pacientes."""

from datetime import timedelta
from typing import Any

from django.db.models import Count, Max, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.patients.models import Patient
from apps.reports.selectors import patients_for_user
from apps.reports.services.periods import (
    iter_months,
    label_month,
    month_key,
    page_queryset,
    resolve_period,
    safe_int,
)
from apps.reports.services.tenant import resolve_report_organization
from apps.scheduling.models import Appointment


def serialize_patient_risk(patient: Patient, threshold: int) -> dict[str, Any]:
    today = timezone.localdate()
    last = (
        patient.last_appointment.date()
        if getattr(patient, "last_appointment", None)
        else None
    )
    next_appt = (
        patient.next_appointment.date()
        if getattr(patient, "next_appointment", None)
        else None
    )
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


def patients_report(user, params, organization=None) -> dict[str, Any]:
    start, end = resolve_period(params)
    organization = resolve_report_organization(user=user, organization=organization)
    risk_days = safe_int(params.get("risk_days"), 30, 1, 3650)
    today = timezone.localdate()
    cutoff = today - timedelta(days=risk_days)

    patients = patients_for_user(user=user, organization=organization)
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
    active_with_appointment = (
        active.filter(
            appointments__organization=organization,
            appointments__start_time__date__range=(start, end),
        )
        .distinct()
        .count()
    )
    retention = (
        round((active_with_appointment / active_total) * 100, 1)
        if active_total
        else 0
    )

    monthly = {
        month_key(month): {
            "month": month_key(month),
            "label": label_month(month),
            "value": 0,
        }
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
    by_professional = [
        {"label": row["therapist__full_name"] or "Sem profissional", "value": row["value"]}
        for row in patients.values("therapist__full_name")
        .annotate(value=Count("id"))
        .order_by("therapist__full_name")
    ]

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
    age_distribution = [
        {"label": label, "value": 0} for _, _, label in age_buckets
    ]
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
        last_appointment=Max(
            "appointments__start_time",
            filter=Q(
                appointments__organization=organization,
                appointments__status=Appointment.Status.COMPLETED,
            ),
        ),
        next_appointment=Max(
            "appointments__start_time",
            filter=Q(
                appointments__organization=organization,
                appointments__start_time__date__gte=today,
                appointments__status__in=[
                    Appointment.Status.SCHEDULED,
                    Appointment.Status.CONFIRMED,
                ],
            ),
        ),
    ).filter(
        Q(last_appointment__date__lt=cutoff)
        | Q(last_appointment__isnull=True)
    )

    status_filter = params.get("status")
    professional_filter = params.get("professional")
    if status_filter and status_filter != "all":
        risk_query = risk_query.filter(status=status_filter)
    if professional_filter and professional_filter != "all":
        risk_query = risk_query.filter(therapist_id=professional_filter)

    paginated = page_queryset(
        risk_query.order_by("last_appointment", "full_name"),
        params,
    )
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
            "results": [
                serialize_patient_risk(item, risk_days)
                for item in paginated["items"]
            ],
        },
    }
