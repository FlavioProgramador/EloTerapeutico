from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from .communication import Communication
from .template import CommunicationTemplate


class CommunicationAutomation(models.Model):
    class DelayUnit(models.TextChoices):
        MINUTES = "minutes", "Minutos"
        HOURS = "hours", "Horas"
        DAYS = "days", "Dias"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communication_automations",
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=80, db_index=True)
    channel = models.CharField(max_length=24, choices=Communication.Channel.choices)
    template = models.ForeignKey(CommunicationTemplate, on_delete=models.PROTECT, related_name="automations")
    is_active = models.BooleanField(default=False, db_index=True)
    delay_value = models.PositiveIntegerField(default=0)
    delay_unit = models.CharField(max_length=12, choices=DelayUnit.choices, default=DelayUnit.MINUTES)
    send_before_event = models.BooleanField(default=False)
    conditions = models.JSONField(default=list, blank=True)
    allowed_start_time = models.TimeField(null=True, blank=True)
    allowed_end_time = models.TimeField(null=True, blank=True)
    allowed_weekdays = models.JSONField(default=list, blank=True)
    respect_preferences = models.BooleanField(default=True)
    max_executions = models.PositiveIntegerField(null=True, blank=True)
    priority = models.CharField(max_length=12, choices=Communication.Priority.choices, default=Communication.Priority.NORMAL)
    fallback_channel = models.CharField(max_length=24, choices=Communication.Channel.choices, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_communication_automations",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_communication_automations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["owner", "is_active", "event_type"], name="comm_auto_event_idx")]


class CommunicationAutomationRun(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", "Iniciada"
        CREATED = "created", "Comunicação criada"
        SKIPPED = "skipped", "Ignorada"
        FAILED = "failed", "Falhou"

    automation = models.ForeignKey(CommunicationAutomation, on_delete=models.CASCADE, related_name="runs")
    source_event = models.CharField(max_length=80)
    source_object_type = models.CharField(max_length=80, blank=True)
    source_object_id = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)
    skip_reason = models.CharField(max_length=255, blank=True)
    communication = models.ForeignKey(
        Communication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="automation_runs",
    )
    idempotency_key = models.CharField(max_length=160)
    error_message = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["automation", "idempotency_key"], name="comm_auto_run_idem_uniq")
        ]
