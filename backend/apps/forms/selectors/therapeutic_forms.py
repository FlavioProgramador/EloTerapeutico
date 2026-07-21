"""Selectors de formulários terapêuticos."""

from django.db.models import Count, Q, QuerySet

from apps.forms.models import TherapeuticForm
from apps.organizations.models import OrganizationMembership

ALLOWED_ORDERING = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
}


def _base_queryset():
    return (
        TherapeuticForm.objects.select_related(
            "organization",
            "created_by",
            "updated_by",
            "source_template",
            "owner",
        )
        .prefetch_related("fields")
        .annotate(submissions_total=Count("submissions"))
    )


def forms_for_owner(*, owner, organization=None) -> QuerySet[TherapeuticForm]:
    queryset = _base_queryset().filter(owner=owner)
    return queryset.filter(organization=organization) if organization else queryset


def forms_for_user(*, user, organization) -> QuerySet[TherapeuticForm]:
    membership = OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = _base_queryset().filter(organization=organization)
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(owner=user)
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.VIEWER,
    }:
        return queryset
    return queryset.none()


def filtered_forms_for_owner(*, owner, params, organization=None) -> QuerySet[TherapeuticForm]:
    queryset = forms_for_owner(owner=owner, organization=organization)
    return _apply_filters(queryset, params)


def filtered_forms_for_user(*, user, organization, params) -> QuerySet[TherapeuticForm]:
    return _apply_filters(forms_for_user(user=user, organization=organization), params)


def _apply_filters(queryset, params):
    search = params.get("search", "").strip()
    status_filter = params.get("status", "").strip()
    category = params.get("category", "").strip()
    ordering = params.get("ordering", "-updated_at")
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(category__icontains=search)
        )
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if category:
        queryset = queryset.filter(category=category)
    return queryset.order_by(
        ordering if ordering in ALLOWED_ORDERING else "-updated_at"
    )
