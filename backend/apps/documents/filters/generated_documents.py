"""Filtros de documentos gerados."""

from django.db.models import Q
from django_filters import rest_framework as filters

from apps.documents.models import GeneratedDocument


class GeneratedDocumentFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = GeneratedDocument
        fields = ("patient", "professional", "document_type", "category", "status")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(document_number__icontains=value)
            | Q(patient__full_name__icontains=value)
            | Q(patient__social_name__icontains=value)
        )
