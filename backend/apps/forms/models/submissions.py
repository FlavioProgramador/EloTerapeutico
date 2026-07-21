"""Modelos de submissões e respostas de formulários."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .therapeutic import FormField, TherapeuticForm


class FormSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SUBMITTED = "submitted", "Enviado"
        REVIEWED = "reviewed", "Revisado"
        ARCHIVED = "archived", "Arquivado"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="form_submissions",
        db_index=True,
    )
    form = models.ForeignKey(
        TherapeuticForm,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="form_submissions",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="form_submissions",
    )
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="form_submissions_as_professional",
    )
    appointment = models.ForeignKey(
        "agenda.Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="form_submissions",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="form_submissions_sent",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "status"],
                name="submission_org_status_idx",
            ),
            models.Index(
                fields=["owner", "status"],
                name="submission_owner_status_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if self.form_id and self.form.organization_id != self.organization_id:
            raise ValidationError({"form": "O formulário pertence a outra organização."})
        if self.patient_id and self.patient.organization_id != self.organization_id:
            raise ValidationError({"patient": "O paciente pertence a outra organização."})
        if self.appointment_id:
            if self.appointment.organization_id != self.organization_id:
                raise ValidationError({"appointment": "A consulta pertence a outra organização."})
            if self.patient_id and self.appointment.patient_id != self.patient_id:
                raise ValidationError({"appointment": "A consulta pertence a outro paciente."})

    def submit(self, user) -> None:
        self.status = self.Status.SUBMITTED
        self.submitted_by = user
        self.submitted_at = timezone.now()
        self.save(
            update_fields=["status", "submitted_by", "submitted_at", "updated_at"]
        )


class FormAnswer(models.Model):
    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    field = models.ForeignKey(
        FormField,
        on_delete=models.PROTECT,
        related_name="answers",
    )
    value = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["field__order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "field"],
                name="unique_form_answer_field",
            )
        ]

    def clean(self):
        super().clean()
        if self.submission_id and self.field_id:
            if self.field.form_id != self.submission.form_id:
                raise ValidationError(
                    {"field": "O campo não pertence ao formulário da submissão."}
                )
