"""Selectors de templates de evolução clínica."""

from django.db.models import Q, QuerySet

from apps.records.models.templates import ClinicalEvolutionTemplate


def clinical_templates_for_user(*, user, params=None) -> QuerySet[ClinicalEvolutionTemplate]:
    queryset = ClinicalEvolutionTemplate.objects.filter(
        Q(owner=user) | Q(owner__isnull=True)
    ).select_related("owner")
    params = params or {}
    if params.get("include_inactive") != "true":
        queryset = queryset.filter(is_active=True, archived_at__isnull=True)
    status_filter = params.get("status")
    if status_filter == "active":
        queryset = queryset.filter(is_active=True, archived_at__isnull=True)
    elif status_filter == "inactive":
        queryset = queryset.filter(is_active=False, archived_at__isnull=True)
    elif status_filter == "archived":
        queryset = queryset.filter(archived_at__isnull=False)
    search = params.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__icontains=search)
            | Q(specialty__icontains=search)
        )
    category = params.get("category", "").strip()
    specialty = params.get("specialty", "").strip()
    if category:
        queryset = queryset.filter(category=category)
    if specialty:
        queryset = queryset.filter(specialty=specialty)
    return queryset
