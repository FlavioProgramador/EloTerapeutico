"""Filtros de bloqueios de horário."""

from django_filters import rest_framework as filters

from apps.scheduling.models import ScheduleBlock


class ScheduleBlockFilter(filters.FilterSet):
    start_time_gte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_time_lte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="lte")

    class Meta:
        model = ScheduleBlock
        fields = ["therapist", "reason", "is_active", "start_time_gte", "start_time_lte"]


__all__ = ["ScheduleBlockFilter"]
