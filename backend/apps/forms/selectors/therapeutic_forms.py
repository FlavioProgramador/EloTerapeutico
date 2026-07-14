"""Selectors de formulários terapêuticos."""

from django.db.models import Count, Q, QuerySet

from apps.forms.models import TherapeuticForm

ALLOWED_ORDERING = {"name", "-name", "created_at", "-created_at", "updated_at", "-updated_at"}


def forms_for_owner(*, owner) -> QuerySet[TherapeuticForm]:
    return (
        TherapeuticForm.objects.filter(owner=owner)
        .select_related("created_by", "updated_by", "source_template")
        .prefetch_related("fields")
        .annotate(submissions_total=Count("submissions"))
    )


def filtered_forms_for_owner(*, owner, params) -> QuerySet[TherapeuticForm]:
    queryset = forms_for_owner(owner=owner)
    search = params.get("search", "").strip()
    status_filter = params.get("status", "").strip()
    category = params.get("category", "").strip()
    ordering = params.get("ordering", "-updated_at")
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search) | Q(category__icontains=search)
        )
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category:
        queryset = queryset.filter(category=category)
    return queryset.order_by(ordering if ordering in ALLOWED_ORDERING else "-updated_at")
