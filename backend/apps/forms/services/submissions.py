"""Casos de uso de submissões e respostas."""

from __future__ import annotations

from django.db import transaction

from apps.forms.exceptions import FinalizedSubmissionError, InvalidFormAnswerError
from apps.forms.models import FormAnswer, FormSubmission, TherapeuticForm


def replace_submission_answers(*, submission: FormSubmission, raw_answers: list[dict]) -> None:
    fields = {field.id: field for field in submission.form.fields.all()}
    answers = []
    for answer in raw_answers:
        field = fields.get(answer["field"])
        if not field:
            raise InvalidFormAnswerError("Campo inválido para este formulário.")
        answers.append(FormAnswer(submission=submission, field=field, value=answer.get("value")))
    submission.answers.all().delete()
    FormAnswer.objects.bulk_create(answers)


@transaction.atomic
def create_submission(
    *,
    form: TherapeuticForm,
    validated_data: dict,
) -> FormSubmission:
    raw_answers = validated_data.pop("answers", [])
    submission = FormSubmission.objects.create(
        form=form,
        owner=form.owner,
        **validated_data,
    )
    replace_submission_answers(submission=submission, raw_answers=raw_answers)
    return submission


@transaction.atomic
def update_submission(
    *,
    submission: FormSubmission,
    validated_data: dict,
) -> FormSubmission:
    submission = FormSubmission.objects.select_for_update().get(pk=submission.pk)
    if submission.status != FormSubmission.Status.DRAFT:
        raise FinalizedSubmissionError("Somente rascunhos podem ser alterados.")
    raw_answers = validated_data.pop("answers", None)
    for attr, value in validated_data.items():
        setattr(submission, attr, value)
    submission.save()
    if raw_answers is not None:
        replace_submission_answers(submission=submission, raw_answers=raw_answers)
    return submission


@transaction.atomic
def submit_form_submission(*, actor, submission: FormSubmission) -> FormSubmission:
    submission = FormSubmission.objects.select_for_update().get(pk=submission.pk)
    if submission.status != FormSubmission.Status.DRAFT:
        raise FinalizedSubmissionError("Este formulário já foi finalizado.")
    submission.submit(actor)
    return submission
