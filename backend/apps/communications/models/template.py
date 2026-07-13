from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from .communication import Communication


class CommunicationTemplate(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="communication_templates",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=40, choices=Communication.Category.choices)
    channel = models.CharField(max_length=24, choices=Communication.Channel.choices)
    subject_template = models.CharField(max_length=255, blank=True)
    body_template = models.TextField()
    allowed_variables = models.JSONField(default=list, blank=True)
    is_system_template = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_communication_templates",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_communication_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "slug", "channel"], name="comm_template_owner_slug_uniq"),
            models.UniqueConstraint(
                fields=["slug", "channel"],
                condition=Q(owner__isnull=True),
                name="comm_system_template_slug_uniq",
            ),
            models.CheckConstraint(
                condition=(Q(is_system_template=False) | Q(owner__isnull=True)),
                name="comm_system_template_without_owner",
            ),
        ]
        indexes = [models.Index(fields=["owner", "is_active", "is_archived"], name="comm_template_owner_idx")]

    def __str__(self) -> str:
        return self.name
