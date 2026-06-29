from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.utils import timezone

from apps.agenda.models import Appointment
from apps.records.models import Anamnesis, Evolution


def annotate_dashboard(queryset):
    now = timezone.now()
    last_appointment = Appointment.objects.filter(
        patient=OuterRef("pk"),
        start_time__lt=now,
    ).exclude(status__in=["cancelled", "rescheduled"]).order_by("-start_time")
    next_appointment = Appointment.objects.filter(
        patient=OuterRef("pk"),
        start_time__gte=now,
        status__in=["scheduled", "confirmed"],
    ).order_by("start_time")
    latest_evolution = Evolution.objects.filter(
        patient=OuterRef("pk")
    ).order_by("-session_date", "-created_at")

    return queryset.select_related("therapist").annotate(
        last_session=Subquery(last_appointment.values("start_time")[:1]),
        next_session=Subquery(next_appointment.values("start_time")[:1]),
        next_session_status=Subquery(next_appointment.values("status")[:1]),
        latest_evolution_at=Subquery(latest_evolution.values("created_at")[:1]),
        latest_evolution_id=Subquery(latest_evolution.values("id")[:1]),
        total_sessions=Count(
            "appointments",
            filter=~Q(appointments__status__in=["cancelled", "rescheduled"]),
            distinct=True,
        ),
        missed_sessions=Count(
            "appointments",
            filter=Q(appointments__status="missed"),
            distinct=True,
        ),
        documents_count=Count(
            "clinical_documents",
            filter=Q(clinical_documents__is_archived=False),
            distinct=True,
        ),
        active_goals_count=Count(
            "treatment_goals",
            filter=Q(treatment_goals__status="active"),
            distinct=True,
        ),
        has_anamnesis=Exists(Anamnesis.objects.filter(patient=OuterRef("pk"))),
    )
