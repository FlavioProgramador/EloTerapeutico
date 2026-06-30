"""Filtros validados e paginados para a listagem de pacientes."""

from django.db.models import Q
from django.utils import timezone
from django_filters import rest_framework as filters

from .models import Patient


class PatientFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    status = filters.MultipleChoiceFilter(choices=Patient.Status.choices)
    therapist = filters.NumberFilter(field_name="therapist_id")
    professional = filters.NumberFilter(method="filter_professional")
    payer_type = filters.ChoiceFilter(choices=Patient.PayerType.choices)
    insurance = filters.CharFilter(field_name="insurance_name", lookup_expr="icontains")
    created_from = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_to = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    birthday_month = filters.NumberFilter(method="filter_birthday_month")
    birthdays = filters.BooleanFilter(method="filter_birthdays")
    reminders_enabled = filters.BooleanFilter()

    class Meta:
        model = Patient
        fields = [
            "status",
            "therapist",
            "professional",
            "payer_type",
            "insurance",
            "created_from",
            "created_to",
            "birthday_month",
            "birthdays",
            "reminders_enabled",
        ]

    def filter_search(self, queryset, name, value):
        term = (value or "").strip()
        if not term:
            return queryset
        digits = "".join(filter(str.isdigit, term))
        criteria = (
            Q(full_name__icontains=term)
            | Q(social_name__icontains=term)
            | Q(email__icontains=term)
        )
        if digits:
            criteria |= Q(cpf__icontains=digits) | Q(phone__icontains=digits) | Q(whatsapp__icontains=digits)
        return queryset.filter(criteria)

    def filter_professional(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(therapist_id=value)
            | Q(professional_links__professional_id=value, professional_links__is_active=True)
        ).distinct()

    def filter_birthday_month(self, queryset, name, value):
        if not value or value < 1 or value > 12:
            return queryset.none() if value else queryset
        return queryset.filter(birth_date__month=value)

    def filter_birthdays(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(birth_date__month=timezone.localdate().month)
