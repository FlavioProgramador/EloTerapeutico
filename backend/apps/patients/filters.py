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
    modality = filters.ChoiceFilter(choices=Patient.Modality.choices)
    payer_type = filters.ChoiceFilter(choices=Patient.PayerType.choices)
    attendance_type = filters.ChoiceFilter(choices=Patient.AttendanceType.choices)
    insurance = filters.CharFilter(
        field_name="insurance_name",
        lookup_expr="icontains",
    )
    tag = filters.CharFilter(method="filter_tag")
    no_next_session = filters.BooleanFilter(method="filter_no_next_session")
    has_anamnesis = filters.BooleanFilter(field_name="has_anamnesis")
    birth_date_gte = filters.DateFilter(
        field_name="birth_date",
        lookup_expr="gte",
    )
    birth_date_lte = filters.DateFilter(
        field_name="birth_date",
        lookup_expr="lte",
    )
    created_from = filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_to = filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )
    created_at_gte = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_at_lte = filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )
    birthday_month = filters.NumberFilter(method="filter_birthday_month")
    birthdays = filters.BooleanFilter(method="filter_birthdays")
    reminders_enabled = filters.BooleanFilter()

    class Meta:
        model = Patient
        fields = [
            "status",
            "therapist",
            "professional",
            "modality",
            "payer_type",
            "attendance_type",
            "insurance",
            "birth_date_gte",
            "birth_date_lte",
            "created_from",
            "created_to",
            "created_at_gte",
            "created_at_lte",
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
            | Q(phone__icontains=term)
            | Q(whatsapp__icontains=term)
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

            criteria |= Q(cpf__icontains=digits)
            for phone_value in phone_variants:
                criteria |= (
                    Q(phone__icontains=phone_value)
                    | Q(whatsapp__icontains=phone_value)
                )

        return queryset.filter(criteria).distinct()

    def filter_professional(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(therapist_id=value)
            | Q(
                professional_links__professional_id=value,
                professional_links__is_active=True,
            )
        ).distinct()

    def filter_tag(self, queryset, name, value):
        return queryset.filter(tags__icontains=value) if value else queryset

    def filter_no_next_session(self, queryset, name, value):
        if value in (None, ""):
            return queryset
        return queryset.filter(next_session__isnull=value)

    def filter_birthday_month(self, queryset, name, value):
        if not value or value < 1 or value > 12:
            return queryset.none() if value else queryset
        return queryset.filter(birth_date__month=value)

    def filter_birthdays(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            birth_date__month=timezone.localdate().month,
        )
