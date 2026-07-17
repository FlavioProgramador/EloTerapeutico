from __future__ import annotations

from django.conf import settings
from django.db import models


class FeatureUsage(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feature_usages",
    )
    feature_key = models.CharField(max_length=80)
    usage_count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "feature_key", "period_start", "period_end")
        ordering = ["-period_start"]
        verbose_name = "Uso de recurso"
        verbose_name_plural = "Uso de recursos"

    def __str__(self) -> str:
        return f"{self.user} — {self.feature_key}: {self.usage_count}"
