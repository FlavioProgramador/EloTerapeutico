"""Modelos de sequenciamento documental."""

from django.conf import settings
from django.db import models


class DocumentSequence(models.Model):
    """Sequência transacional por profissional e ano para numeração documental."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_sequences",
    )
    year = models.PositiveSmallIntegerField()
    last_value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "year"],
                name="unique_document_sequence_owner_year",
            )
        ]
