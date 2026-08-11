"""Casos de uso de submissões e respostas."""

from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.forms.exceptions import FinalizedSubmissionError, InvalidFormAnswerError
from apps.forms.models import FormAnswer, FormSubmission, TherapeuticForm
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability


def _ensure_access(*, actor, organization, submission=None):
    if actor is None:
        return None
    membership = OrganizationMembership.objects.filter(
        user=actor,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    if membership is None or not has_capability(membership, "forms.manage"):
        raise PermissionDenied("Você não pode gerenciar submissões nesta organização.")
    if (
        membership.role == OrganizationMembership.Role.THERAPIST
        and submission is not None
        and submission.owner_id != actor.pk
        and submission.professional_id != actor.pk
    ):
        raise PermissionDenied("A submissão pertence a outro profissional.")
    return membership


def replace_submission_answers(
    *,
    submission: FormSubmission,
    raw_answers: list[dict],
) -> None:
    fields = {field.id: field for field in submission.form.fields.all()}
    answers = []
    for answer in raw_answers:
        field = fields.get(answer["field"])
        if not field:
            raise InvalidFormAnswerError("Campo inválido para este formulário.")
        answers.append(
            FormAnswer(
                submission=submission,
                field=field,
                value=answer.get("value"),
            )
        )
    submission.answers.all().delete()
    FormAnswer.objects.bulk_create(answers)


@transaction.atomic
def create_submission(
    *,
    form: TherapeuticForm,
    validated_data: dict,
    actor=None,
) -> FormSubmission:
    _ensure_access(actor=actor, organization=form.organization)
    raw_answers = validated_data.pop("answers", [])
    submission = FormSubmission(
        organization=form.organization,
        form=form,
        owner=form.owner,
        **validated_data,
    )
    submission.full_clean()
    submission.save()
    replace_submission_answers(
        submission=submission,
        raw_answers=raw_answers,
    )
    return submission


@transaction.atomic
def update_submission(
    *,
    submission: FormSubmission,
    validated_data: dict,
    actor=None,
) -> FormSubmission:
    submission = FormSubmission.objects.select_for_update().select_related(
        "organization",
        "form",
        "patient",
        "appointment",
    ).get(pk=submission.pk)
    _ensure_access(
        actor=actor,
        organization=submission.organization,
        submission=submission,
    )
    if submission.status != FormSubmission.Status.DRAFT:
        raise FinalizedSubmissionError("Somente rascunhos podem ser alterados.")
    raw_answers = validated_data.pop("answers", None)
    for attr, value in validated_data.items():
        setattr(submission, attr, value)
    submission.full_clean()
    submission.save()
    if raw_answers is not None:
        replace_submission_answers(
            submission=submission,
            raw_answers=raw_answers,
        )
    return submission


@transaction.atomic
def submit_form_submission(*, actor, submission: FormSubmission) -> FormSubmission:
    submission = FormSubmission.objects.select_for_update().select_related(
        "organization"
    ).get(pk=submission.pk)
    _ensure_access(
        actor=actor,
        organization=submission.organization,
        submission=submission,
    )
    if submission.status != FormSubmission.Status.DRAFT:
        raise FinalizedSubmissionError("Este formulário já foi finalizado.")
    submission.submit(actor)
    return submission
