"""Selectors de pacientes para relatórios."""

from django.db.models import QuerySet

from apps.patients.models import Patient


def patients_for_owner(*, owner) -> QuerySet[Patient]:
    return Patient.objects.filter(therapist=owner).select_related("therapist")
