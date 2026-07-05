"""Filtros de consulta do módulo financeiro."""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import FinancialTransaction


class FinancialTransactionFilter(filters.FilterSet):
    created_at_gte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    due_date_gte = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_date_lte = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    start_date = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")
    recurring = filters.BooleanFilter(field_name="is_recurring")

    class Meta:
        model = FinancialTransaction
        fields = [
            "transaction_type",
            "payment_status",
            "payment_method",
            "category",
            "category_ref",
            "patient",
            "therapist",
            "source",
            "beneficiary",
            "recurring",
            "created_at_gte",
            "created_at_lte",
            "due_date_gte",
            "due_date_lte",
            "start_date",
            "end_date",
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(description__icontains=value)
            | Q(beneficiary__icontains=value)
            | Q(patient__full_name__icontains=value)
        )
