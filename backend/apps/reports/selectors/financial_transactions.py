"""Selectors de transações e recorrências financeiras para relatórios."""

from datetime import date

from django.db.models import Q, QuerySet

from apps.agenda.models import PatientPackage
from apps.financeiro.models import FinancialTransaction, MonthlySubscription


def transactions_for_period(*, owner, start: date, end: date) -> QuerySet[FinancialTransaction]:
    return (
        FinancialTransaction.objects.filter(therapist=owner)
        .filter(
            Q(due_date__range=(start, end))
            | Q(paid_at__date__range=(start, end))
            | Q(created_at__date__range=(start, end))
        )
        .select_related("patient")
    )


def all_transactions_for_owner(*, owner) -> QuerySet[FinancialTransaction]:
    return FinancialTransaction.objects.filter(therapist=owner).select_related("patient")


def active_subscriptions_for_owner(*, owner) -> QuerySet[MonthlySubscription]:
    return MonthlySubscription.objects.filter(
        therapist=owner,
        status=MonthlySubscription.Status.ACTIVE,
    )


def active_packages_for_owner(*, owner) -> QuerySet[PatientPackage]:
    return PatientPackage.objects.filter(
        therapist=owner,
        status=PatientPackage.Status.ACTIVE,
    )
