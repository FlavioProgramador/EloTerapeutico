"""Selectors de mensalidades recorrentes de pacientes."""

from apps.finances.models import MonthlySubscription


def monthly_subscriptions_accessible_to(user, *, status=None):
    queryset = MonthlySubscription.objects.select_related("patient", "therapist")
    if not user or user.is_anonymous:
        return queryset.none()
    if not (user.is_admin_role or user.is_secretary):
        queryset = queryset.filter(therapist=user)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def active_monthly_subscriptions_for(*, owner):
    return MonthlySubscription.objects.filter(
        therapist=owner, status=MonthlySubscription.Status.ACTIVE
    ).select_related("patient")
