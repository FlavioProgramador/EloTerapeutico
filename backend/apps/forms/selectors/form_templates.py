"""Selectors da biblioteca de templates de formulários."""

from django.db.models import Q, QuerySet

from apps.forms.models import FormTemplate


def active_form_templates(*, params=None) -> QuerySet[FormTemplate]:
    queryset = FormTemplate.objects.filter(is_active=True)
    params = params or {}
    search = params.get("search", "").strip()
    category = params.get("category", "").strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search) | Q(category__icontains=search)
        )
    if category:
        queryset = queryset.filter(category=category)
    return queryset
