"""Modelos de submissões e respostas de formulários."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from .therapeutic import FormField, TherapeuticForm


class FormSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SUBMITTED = "submitted", "Enviado"
        REVIEWED = "reviewed", "Revisado"
        ARCHIVED = "archived", "Arquivado"

    form = models.ForeignKey(TherapeuticForm, on_delete=models.PROTECT, related_name="submissions")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_submissions")
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
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
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
        indexes = [models.Index(fields=["owner", "status"], name="submission_owner_status_idx")]

    def submit(self, user) -> None:
        self.status = self.Status.SUBMITTED
        self.submitted_by = user
        self.submitted_at = timezone.now()
        self.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])


class FormAnswer(models.Model):
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name="answers")
    field = models.ForeignKey(FormField, on_delete=models.PROTECT, related_name="answers")
    value = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["field__order", "id"]
        constraints = [models.UniqueConstraint(fields=["submission", "field"], name="unique_form_answer_field")]
