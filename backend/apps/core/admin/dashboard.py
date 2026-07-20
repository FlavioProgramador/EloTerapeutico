"""Callbacks e métricas reais para o dashboard interno do Django Admin."""

from __future__ import annotations

# mypy: ignore-errors
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django.utils import timezone

from apps.documents.models import GeneratedDocument
from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.scheduling.models import Appointment


def _next_month_start(current_date):
    if current_date.month == 12:
        return current_date.replace(year=current_date.year + 1, month=1, day=1)
    return current_date.replace(month=current_date.month + 1, day=1)


def _start_of_day(current_date):
    current_timezone = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(current_date, time.min), current_timezone)


def _format_currency(value: Decimal | None) -> str:
    amount = value or Decimal("0.00")
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _scoped_queryset(
    queryset,
    request,
    *,
    owner_field: str | None = None,
    therapist_field: str | None = None,
):
    """Restringe métricas ao usuário logado quando ele não for superusuário."""

    user = request.user
    if user.is_superuser:
        return queryset
    if owner_field:
        return queryset.filter(**{owner_field: user})
    if therapist_field:
        return queryset.filter(**{therapist_field: user})
    return queryset.none()


def dashboard_callback(request, context):
    """Monta cards do painel inicial usando apenas dados reais do banco."""

    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    month_start = today.replace(day=1)
    next_month = _next_month_start(today)
    recent_cutoff = timezone.now() - timedelta(days=7)

    today_start = _start_of_day(today)
    tomorrow_start = today_start + timedelta(days=1)
    week_start_at = _start_of_day(week_start)
    week_end_at = _start_of_day(week_end)
    month_start_at = _start_of_day(month_start)

    User = get_user_model()
    users = User.objects.all() if request.user.is_superuser else User.objects.filter(pk=request.user.pk)

    patients = Patient.all_objects.all()
    if not request.user.is_superuser:
        patients = patients.filter(
            Q(therapist=request.user) | Q(professional_links__professional=request.user)
        ).distinct()

    search_query = request.GET.get("q", "").strip()
    found_patients = []
    found_therapists = []

    if search_query:
        found_patients = patients.filter(
            Q(full_name__icontains=search_query)
            | Q(social_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
            | Q(cpf__icontains=search_query)
        )[:10]

        found_therapists = users.filter(
            Q(full_name__icontains=search_query) | Q(email__icontains=search_query) | Q(phone__icontains=search_query)
        )[:10]

    appointments = _scoped_queryset(
        Appointment.objects.all(),
        request,
        therapist_field="therapist",
    )
    transactions = _scoped_queryset(
        FinancialTransaction.objects.all(),
        request,
        therapist_field="therapist",
    )
    evolutions = _scoped_queryset(
        Evolution.objects.all(),
        request,
        owner_field="created_by",
    )
    documents = _scoped_queryset(
        GeneratedDocument.objects.all(),
        request,
        owner_field="owner",
    )

    monthly_paid = transactions.filter(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        due_date__gte=month_start,
        due_date__lt=next_month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    monthly_pending = transactions.filter(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ],
        due_date__gte=month_start,
        due_date__lt=next_month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    monthly_total_income = monthly_paid + monthly_pending
    if monthly_total_income > 0:
        monthly_percentage = int((monthly_paid / monthly_total_income) * 100)
    else:
        monthly_percentage = 0

    monthly_revenue = monthly_paid

    pending_amount = transactions.filter(
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ]
    ).aggregate(total=Sum("amount"))["total"]

    context.update(
        {
            "dashboard_cards": [
                {
                    "label": "Pacientes cadastrados",
                    "value": patients.count(),
                    "description": "Total real incluindo arquivados para auditoria.",
                    "icon": "groups",
                },
                {
                    "label": "Pacientes ativos",
                    "value": patients.filter(
                        is_active=True,
                        deleted_at__isnull=True,
                    ).count(),
                    "description": "Pacientes disponíveis no atendimento.",
                    "icon": "person_check",
                },
                {
                    "label": "Terapeutas cadastrados",
                    "value": users.filter(role=User.Role.THERAPIST).count(),
                    "description": "Usuários com papel de terapeuta.",
                    "icon": "psychology",
                },
                {
                    "label": "Agendamentos de hoje",
                    "value": appointments.filter(
                        start_time__gte=today_start,
                        start_time__lt=tomorrow_start,
                    ).count(),
                    "description": "Sessões marcadas para hoje.",
                    "icon": "today",
                },
                {
                    "label": "Agendamentos da semana",
                    "value": appointments.filter(
                        start_time__gte=week_start_at,
                        start_time__lt=week_end_at,
                    ).count(),
                    "description": "Janela de segunda a domingo.",
                    "icon": "event",
                },
                {
                    "label": "Receita paga do mês",
                    "value": _format_currency(monthly_revenue),
                    "description": "Somente receitas pagas no mês corrente.",
                    "icon": "payments",
                },
                {
                    "label": "Pagamentos pendentes",
                    "value": _format_currency(pending_amount),
                    "description": "Valores pendentes ou parcialmente pagos.",
                    "icon": "pending_actions",
                },
                {
                    "label": "Prontuários recentes",
                    "value": evolutions.filter(updated_at__gte=recent_cutoff).count(),
                    "description": "Evoluções atualizadas nos últimos 7 dias.",
                    "icon": "clinical_notes",
                },
                {
                    "label": "Novos cadastros no mês",
                    "value": patients.filter(created_at__gte=month_start_at).count(),
                    "description": "Pacientes criados no mês atual.",
                    "icon": "person_add",
                },
                {
                    "label": "Documentos clínicos enviados",
                    "value": documents.filter(
                        status=GeneratedDocument.Status.COMPLETED,
                        generated_at__isnull=False,
                    ).count(),
                    "description": "Documentos gerados com sucesso.",
                    "icon": "description",
                },
            ],
            "dashboard_generated_at": timezone.now(),
            "search_query": search_query,
            "found_patients": found_patients,
            "found_therapists": found_therapists,
            "monthly_paid_formatted": _format_currency(monthly_paid),
            "monthly_total_formatted": _format_currency(monthly_total_income),
            "monthly_percentage": monthly_percentage,
        }
    )
    return context


def environment_callback(request):
    """Exibe um selo simples para diferenciar ambientes no backoffice."""

    if settings.DEBUG:
        return ["Desenvolvimento", "warning"]
    return ["Produção", "success"]
