# mypy: ignore-errors
"""Modelos específicos do fluxo compacto de evolução clínica."""

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField


class ClinicalEvolutionTemplate(models.Model):
    """Template Markdown privado do profissional para registros de evolução."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="clinical_evolution_templates",
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    specialty = models.CharField(max_length=120, blank=True, db_index=True)
    content = EncryptedTextField()
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0)
    usage_count = models.PositiveIntegerField(default=0)
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_clinical_template_owner_name",
            )
        ]
        permissions = [
            (
                "manage_system_clinical_templates",
                "Can manage system clinical evolution templates",
            )
        ]

    def __str__(self):
        scope = self.owner.full_name if self.owner_id else "Sistema"
        return f"{self.name} ({scope})"
