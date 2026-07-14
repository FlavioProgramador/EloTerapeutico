"""Selectors de submissões de formulários."""

from django.db.models import QuerySet

from apps.forms.models import FormSubmission, TherapeuticForm


def submissions_for_form(*, form: TherapeuticForm) -> QuerySet[FormSubmission]:
    return form.submissions.select_related("patient", "professional", "submitted_by").prefetch_related(
        "answers", "answers__field"
    )


def submissions_for_owner(*, owner) -> QuerySet[FormSubmission]:
    return FormSubmission.objects.filter(owner=owner).select_related(
        "form", "patient", "professional"
    ).prefetch_related("answers", "answers__field")
