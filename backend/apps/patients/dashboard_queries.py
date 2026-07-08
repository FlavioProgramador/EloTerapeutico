# mypy: ignore-errors
from django.db.models import (
    CharField,
    Count,
    DateTimeField,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.utils import timezone

from apps.agenda.models import Appointment
from apps.records.models import Anamnesis, Evolution


def annotate_essential(queryset):
    """
    Aplica anotações leves necessárias para filtros e listagem básica.
    Provê valores padrão para campos pesados para manter compatibilidade de contrato.
    """
    now = timezone.now()
    next_appointment = Appointment.objects.filter(
        patient=OuterRef("pk"),
        start_time__gte=now,
        status__in=["scheduled", "confirmed"],
    ).order_by("start_time")

    return queryset.select_related("therapist").annotate(
        next_session=Subquery(next_appointment.values("start_time")[:1]),
        has_anamnesis=Exists(Anamnesis.objects.filter(patient=OuterRef("pk"))),
        # Valores padrão para manter contrato sem custo de subquery/count
        last_session=Value(None, output_field=DateTimeField()),
        next_session_status=Value(None, output_field=CharField()),
        latest_evolution_at=Value(None, output_field=DateTimeField()),
        latest_evolution_id=Value(None, output_field=IntegerField()),
        total_sessions=Value(0, output_field=IntegerField()),
        missed_sessions=Value(0, output_field=IntegerField()),
        documents_count=Value(0, output_field=IntegerField()),
        active_goals_count=Value(0, output_field=IntegerField()),
    )


def annotate_heavy(queryset):
    """Aplica anotações pesadas (subqueries e counts complexos) para o dashboard."""
    now = timezone.now()
    last_appointment = (
        Appointment.objects.filter(
            patient=OuterRef("pk"),
            start_time__lt=now,
        )
        .exclude(status__in=["cancelled", "rescheduled"])
        .order_by("-start_time")
    )

    next_appointment = Appointment.objects.filter(
        patient=OuterRef("pk"),
        start_time__gte=now,
        status__in=["scheduled", "confirmed"],
    ).order_by("start_time")

    latest_evolution = Evolution.objects.filter(patient=OuterRef("pk")).order_by("-session_date", "-created_at")

    return queryset.annotate(
        last_session=Subquery(last_appointment.values("start_time")[:1]),
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
    )


def annotate_dashboard(queryset):
    """Aplica todas as anotações reais para o detalhe/dashboard."""
    now = timezone.now()
    next_appointment = Appointment.objects.filter(
        patient=OuterRef("pk"),
        start_time__gte=now,
        status__in=["scheduled", "confirmed"],
    ).order_by("start_time")

    queryset = queryset.select_related("therapist").annotate(
        next_session=Subquery(next_appointment.values("start_time")[:1]),
        has_anamnesis=Exists(Anamnesis.objects.filter(patient=OuterRef("pk"))),
    )
    return annotate_heavy(queryset)
