"""Filtros da API de transações financeiras."""

from django_filters import rest_framework as filters

from apps.finances.models import FinancialTransaction


class FinancialTransactionFilter(filters.FilterSet):
    created_at_gte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.IsoDateTimeFilter(field_name="created_at", lookup_expr="lte")
    due_date_gte = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_date_lte = filters.DateFilter(field_name="due_date", lookup_expr="lte")

    class Meta:
        model = FinancialTransaction
        fields = [
            "transaction_type", "payment_status", "payment_method", "category",
            "patient", "created_at_gte", "created_at_lte", "due_date_gte", "due_date_lte",
        ]
