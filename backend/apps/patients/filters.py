"""Filtros de pesquisa do módulo de pacientes."""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Patient


class PatientFilter(filters.FilterSet):
    birth_date_gte = filters.DateFilter(field_name="birth_date", lookup_expr="gte")
    birth_date_lte = filters.DateFilter(field_name="birth_date", lookup_expr="lte")
    created_at_gte = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")
    tag = filters.CharFilter(method="filter_tag")
    no_next_session = filters.BooleanFilter(method="filter_no_next_session")
    has_anamnesis = filters.BooleanFilter(field_name="has_anamnesis")

    class Meta:
        model = Patient
        fields = [
            "status",
            "therapist",
            "modality",
            "payer_type",
            "attendance_type",
            "birth_date_gte",
            "birth_date_lte",
            "created_at_gte",
            "created_at_lte",
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset

        digits = "".join(filter(str.isdigit, value))
        query = (
            Q(full_name__icontains=value)
            | Q(social_name__icontains=value)
            | Q(email__icontains=value)
            | Q(phone__icontains=value)
            | Q(whatsapp__icontains=value)
        )

        if digits:
            phone_variants = {digits}
            if len(digits) == 10:
                phone_variants.add(
                    f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
                )
            elif len(digits) == 11:
                phone_variants.add(
                    f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
                )

            query |= Q(cpf__contains=digits)
            for phone_value in phone_variants:
                query |= (
                    Q(phone__icontains=phone_value)
                    | Q(whatsapp__icontains=phone_value)
                )

        return queryset.filter(query).distinct()

    def filter_tag(self, queryset, name, value):
        return queryset.filter(tags__icontains=value) if value else queryset

    def filter_no_next_session(self, queryset, name, value):
        return queryset.filter(next_session__isnull=value)
