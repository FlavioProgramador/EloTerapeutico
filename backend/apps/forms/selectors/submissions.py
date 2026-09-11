"""Selectors de submissões de formulários."""

from django.db.models import Q, QuerySet

from apps.forms.models import FormSubmission, TherapeuticForm
from apps.organizations.models import OrganizationMembership


def _base_queryset():
    return FormSubmission.objects.select_related(
        "organization",
        "form",
        "patient",
        "professional",
        "submitted_by",
        "owner",
    ).prefetch_related("answers", "answers__field")


def submissions_for_form(*, form: TherapeuticForm) -> QuerySet[FormSubmission]:
    return _base_queryset().filter(
        form=form,
        organization=form.organization,
    )


def submissions_for_owner(*, owner, organization=None) -> QuerySet[FormSubmission]:
    queryset = _base_queryset().filter(owner=owner)
    return queryset.filter(organization=organization) if organization else queryset


def submissions_for_user(*, user, organization) -> QuerySet[FormSubmission]:
    membership = OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = _base_queryset().filter(organization=organization)
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(Q(owner=user) | Q(professional=user))
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.VIEWER,
    }:
        return queryset
    return queryset.none()
