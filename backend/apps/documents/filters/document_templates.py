"""Filtros de templates de documentos."""

from django.db.models import Q
from django_filters import rest_framework as filters

from apps.documents.models import DocumentTemplate


class DocumentTemplateFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = DocumentTemplate
        fields = ("status", "category", "document_type", "specialty")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(category__icontains=value)
            | Q(specialty__icontains=value)
        )
