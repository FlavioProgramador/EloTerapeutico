"""Templates de formulários terapêuticos."""

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .choices import FormCategory


class FormTemplate(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="form_templates",
    )
    name = models.CharField(max_length=180, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=32,
        choices=FormCategory.choices,
        db_index=True,
    )
    icon = models.CharField(max_length=64, blank=True)
    fields_schema = models.JSONField(default=list, blank=True)
    is_system_template = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]
        indexes = [
            models.Index(
                fields=["organization", "is_active"],
                name="form_tpl_org_active_idx",
            ),
            models.Index(
                fields=["category", "is_active"],
                name="form_tpl_cat_active_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(is_system_template=True, organization__isnull=True)
                    | Q(is_system_template=False, organization__isnull=False)
                ),
                name="form_template_scope_consistent",
            ),
            models.UniqueConstraint(
                fields=["organization", "name"],
                condition=Q(
                    is_system_template=False,
                    organization__isnull=False,
                ),
                name="unique_custom_form_template_org_name",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(
                    is_system_template=True,
                    organization__isnull=True,
                ),
                name="unique_system_form_template_name",
            ),
        ]

    def clean(self):
        super().clean()
        if self.is_system_template and self.organization_id:
            raise ValidationError(
                "Templates do sistema não podem pertencer a uma organização."
            )
        if not self.is_system_template and not self.organization_id:
            raise ValidationError(
                "Templates personalizados exigem uma organização."
            )

    def __str__(self) -> str:
        return self.name
