from __future__ import annotations

from django.db import models


class CommunicationPlanEntitlement(models.Model):
    plan = models.OneToOneField(
        "billing.Plan",
        on_delete=models.CASCADE,
        related_name="communication_entitlement",
    )
    communications_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    custom_templates_enabled = models.BooleanField(default=True)
    automations_enabled = models.BooleanField(default=True)
    advanced_automations_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    sms_enabled = models.BooleanField(default=False)
    metrics_enabled = models.BooleanField(default=True)
    max_communications_per_month = models.PositiveIntegerField(null=True, blank=True, default=500)
    max_email_communications_per_month = models.PositiveIntegerField(null=True, blank=True, default=500)
    max_automations = models.PositiveIntegerField(null=True, blank=True, default=10)
    max_custom_templates = models.PositiveIntegerField(null=True, blank=True, default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Recurso de comunicações por plano"
        verbose_name_plural = "Recursos de comunicações por plano"

    def __str__(self) -> str:
        return f"Comunicações — {self.plan}"
