"""Filtros de pacotes de sessões."""

from django.db import models
from django.db.models import Q
from django_filters import rest_framework as filters

from apps.scheduling.models import PatientPackage


class PackageFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    valid_until_gte = filters.DateFilter(field_name="valid_until", lookup_expr="gte")
    with_balance = filters.BooleanFilter(method="filter_balance")

    class Meta:
        model = PatientPackage
        fields = ["patient", "therapist", "status"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(patient__full_name__icontains=value)
            | Q(patient__social_name__icontains=value)
        )

    def filter_balance(self, queryset, name, value):
        if value:
            return queryset.filter(sessions_used__lt=models.F("sessions_contracted"))
        return queryset.filter(sessions_used__gte=models.F("sessions_contracted"))


__all__ = ["PackageFilter"]
