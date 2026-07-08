from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class FormCategory(models.TextChoices):
    ANAMNESIS = "anamnese", "Anamnese"
    ASSESSMENT = "avaliacao", "Avaliação"
    EVOLUTION = "evolucao", "Evolução"
    SCALES = "escalas", "Escalas"
    QUESTIONNAIRE = "questionario", "Questionário"
    OTHER = "outro", "Outro"


class FieldType(models.TextChoices):
    SHORT_TEXT = "short_text", "Texto curto"
    LONG_TEXT = "long_text", "Texto longo"
    NUMBER = "number", "Número"
    DATE = "date", "Data"
    SELECT = "select", "Seleção"
    RADIO = "radio", "Múltipla escolha"
    CHECKBOX = "checkbox", "Caixas de seleção"
    SCALE = "scale", "Escala"
    HEADING = "heading", "Título"


class FormTemplate(models.Model):
    name = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=FormCategory.choices, db_index=True)
    icon = models.CharField(max_length=64, blank=True)
    fields_schema = models.JSONField(default=list, blank=True)
    is_system_template = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        indexes = [models.Index(fields=["category", "is_active"], name="form_tpl_cat_active_idx")]

    def __str__(self) -> str:
        return self.name


class TherapeuticForm(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        ARCHIVED = "archived", "Arquivado"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forms_created",
    )
    name = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=32, choices=FormCategory.choices, default=FormCategory.OTHER, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    source_template = models.ForeignKey(FormTemplate, null=True, blank=True, on_delete=models.SET_NULL, related_name="forms")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="forms_authored")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="forms_updated")
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "status"], name="form_owner_status_idx"),
            models.Index(fields=["owner", "category"], name="form_owner_category_idx"),
        ]

    def archive(self, user) -> None:
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.updated_by = user
        self.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])

    def restore(self, user) -> None:
        self.status = self.Status.ACTIVE
        self.archived_at = None
        self.updated_by = user
        self.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])

    def __str__(self) -> str:
        return self.name


class FormField(models.Model):
    form = models.ForeignKey(TherapeuticForm, on_delete=models.CASCADE, related_name="fields")
    type = models.CharField(max_length=24, choices=FieldType.choices)
    label = models.CharField(max_length=180)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=255, blank=True)
    required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    is_visible = models.BooleanField(default=True)
    internal_id = models.SlugField(max_length=80, blank=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["form", "order"], name="form_field_order_idx")]

    def __str__(self) -> str:
        return self.label


class FormSubmission(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SUBMITTED = "submitted", "Enviado"
        REVIEWED = "reviewed", "Revisado"
        ARCHIVED = "archived", "Arquivado"

    form = models.ForeignKey(TherapeuticForm, on_delete=models.PROTECT, related_name="submissions")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_submissions")
    patient = models.ForeignKey("patients.Patient", null=True, blank=True, on_delete=models.PROTECT, related_name="form_submissions")
    professional = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="form_submissions_as_professional")
    appointment = models.ForeignKey("agenda.Appointment", null=True, blank=True, on_delete=models.SET_NULL, related_name="form_submissions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="form_submissions_sent")
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
