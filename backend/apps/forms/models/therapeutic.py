"""Modelos de formulários terapêuticos e campos."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .choices import FieldType, FormCategory
from .templates import FormTemplate


class TherapeuticForm(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        ARCHIVED = "archived", "Arquivado"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="therapeutic_forms",
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forms_created",
    )
    name = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=32,
        choices=FormCategory.choices,
        default=FormCategory.OTHER,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    source_template = models.ForeignKey(
        FormTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="forms",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forms_authored",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="forms_updated",
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(
                fields=["organization", "status"],
                name="form_org_status_idx",
            ),
            models.Index(
                fields=["organization", "category"],
                name="form_org_category_idx",
            ),
            models.Index(fields=["owner", "status"], name="form_owner_status_idx"),
            models.Index(fields=["owner", "category"], name="form_owner_category_idx"),
        ]

    def clean(self):
        super().clean()
        if self.source_template_id and (
            not self.source_template.is_system_template
            and self.source_template.organization_id != self.organization_id
        ):
            raise ValidationError(
                {"source_template": "O template pertence a outra organização."}
            )

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
    form = models.ForeignKey(
        TherapeuticForm,
        on_delete=models.CASCADE,
        related_name="fields",
    )
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
        indexes = [
            models.Index(fields=["form", "order"], name="form_field_order_idx")
        ]

    def __str__(self) -> str:
        return self.label
