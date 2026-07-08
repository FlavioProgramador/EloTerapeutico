"""Aditivos imutáveis de evolução clínica."""

from django.conf import settings
from django.db import models

from core.fields import EncryptedTextField


class EvolutionAddendum(models.Model):
    evolution = models.ForeignKey(
        "records.Evolution",
        on_delete=models.PROTECT,
        related_name="addenda",
        verbose_name="Evolução",
    )
    reason = models.TextField(
        verbose_name="Motivo do aditivo",
        help_text="Justificativa clínica ou legal para o complemento.",
    )
    content = EncryptedTextField(
        verbose_name="Conteúdo do aditivo",
        help_text="Texto do complemento à evolução original.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="addenda_created",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Aditivo de Evolução"
        verbose_name_plural = "Aditivos de Evolução"
        ordering = ["created_at"]

    def __str__(self):
        return f"Aditivo #{self.pk} → Evolução #{self.evolution_id} " f"({self.created_at:%d/%m/%Y})"
