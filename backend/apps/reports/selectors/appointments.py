"""Selectors de consultas usadas por relatórios de agenda."""

from datetime import date

from django.db.models import QuerySet

from apps.organizations.models import OrganizationMembership
from apps.scheduling.models import Appointment


def appointments_for_period(
    *,
    start: date,
    end: date,
    user=None,
    organization=None,
    owner=None,
) -> QuerySet[Appointment]:
    if organization is None:
        professional = owner or user
        if professional is None:
            return Appointment.objects.none()
        return (
            Appointment.objects.filter(
                therapist=professional,
                start_time__date__range=(start, end),
            )
            .select_related("patient", "therapist", "room")
            .prefetch_related("financial_transactions")
        )

    membership = OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = Appointment.objects.filter(
        organization=organization,
        start_time__date__range=(start, end),
    )
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        queryset = queryset.filter(therapist=user)
    return (
        queryset.select_related("patient", "therapist", "room")
        .prefetch_related("financial_transactions")
    )
