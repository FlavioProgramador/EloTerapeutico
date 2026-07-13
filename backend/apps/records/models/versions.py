"""Histórico versionado de anamnese e evolução."""

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField


class AnamnesisVersion(models.Model):
    anamnesis = models.ForeignKey(
        "records.Anamnesis",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    snapshot = EncryptedTextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anamnesis_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["anamnesis", "version"],
                name="unique_anamnesis_version",
            )
        ]


class EvolutionVersion(models.Model):
    evolution = models.ForeignKey(
        "records.Evolution",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    snapshot = EncryptedTextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evolution_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["evolution", "version"],
                name="unique_evolution_version",
            )
        ]
