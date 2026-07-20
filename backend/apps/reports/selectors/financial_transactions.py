"""Selectors financeiros consumidos pelo módulo de relatórios."""

from apps.finances.selectors import (
    active_monthly_subscriptions_for,
    transactions_for_owner,
    transactions_for_owner_period,
)
from apps.scheduling.models import PatientPackage


def transactions_for_period(*, owner, start, end):
    return transactions_for_owner_period(owner=owner, start=start, end=end)


def all_transactions_for_owner(*, owner):
    return transactions_for_owner(owner=owner)


def active_subscriptions_for_owner(*, owner):
    return active_monthly_subscriptions_for(owner=owner)


def active_packages_for_owner(*, owner):
    return PatientPackage.objects.filter(
        therapist=owner, status=PatientPackage.Status.ACTIVE
    )
