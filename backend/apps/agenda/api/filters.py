"""Filtros de backend para o módulo de Agenda."""

from django.db import models
from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Appointment, AppointmentRecurrence, PatientPackage, ScheduleBlock


class AppointmentFilter(filters.FilterSet):
    start_time_gte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_time_lte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="lte")
    date = filters.DateFilter(field_name="start_time", lookup_expr="date")
    search = filters.CharFilter(method="filter_search")
    telemedicine = filters.BooleanFilter(method="filter_telemedicine")
    recurring = filters.BooleanFilter(field_name="is_recurring")
    pending_only = filters.BooleanFilter(method="filter_pending")
    confirmed_only = filters.BooleanFilter(method="filter_confirmed")

    class Meta:
        model = Appointment
        fields = [
            "status", "patient", "therapist", "room", "modality",
            "appointment_type", "package", "date", "start_time_gte",
            "start_time_lte", "recurring",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(patient__full_name__icontains=value)
            | Q(patient__social_name__icontains=value)
            | Q(patient__email__icontains=value)
            | Q(patient__phone__icontains=value)
            | Q(patient__cpf__icontains=value)
            | Q(therapist__full_name__icontains=value)
        ).distinct()

    def filter_telemedicine(self, queryset, name, value):
        return queryset.filter(telemedicine_room__isnull=not value)

    def filter_pending(self, queryset, name, value):
        return queryset.filter(status=Appointment.Status.SCHEDULED) if value else queryset

    def filter_confirmed(self, queryset, name, value):
        return queryset.filter(status=Appointment.Status.CONFIRMED) if value else queryset


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


class ScheduleBlockFilter(filters.FilterSet):
    start_time_gte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_time_lte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="lte")

    class Meta:
        model = ScheduleBlock
        fields = ["therapist", "reason", "is_active", "start_time_gte", "start_time_lte"]
