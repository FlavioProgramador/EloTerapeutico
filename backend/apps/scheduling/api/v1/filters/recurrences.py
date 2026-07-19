"""Filtros de recorrências."""

from django.db.models import Q
from django_filters import rest_framework as filters

from apps.scheduling.models import AppointmentRecurrence


class RecurrenceFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    created_gte = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    ends_lte = filters.DateFilter(field_name="ends_on", lookup_expr="lte")

    class Meta:
        model = AppointmentRecurrence
        fields = ["patient", "therapist", "frequency", "status"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(patient__full_name__icontains=value)
            | Q(patient__social_name__icontains=value)
            | Q(therapist__full_name__icontains=value)
        )


__all__ = ["RecurrenceFilter"]
