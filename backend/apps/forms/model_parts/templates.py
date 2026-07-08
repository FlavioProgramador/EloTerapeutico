"""Templates de formulários terapêuticos."""

from django.db import models

from .choices import FormCategory


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
