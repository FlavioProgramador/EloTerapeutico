"""Entidade raiz do tenant do Elo Terapêutico."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Organization(models.Model):
    class Type(models.TextChoices):
        INDIVIDUAL = "individual", "Profissional individual"
        CLINIC = "clinic", "Clínica"
        COMPANY = "company", "Empresa"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        SUSPENDED = "suspended", "Suspensa"
        ARCHIVED = "archived", "Arquivada"

    class OnboardingStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        IN_PROGRESS = "in_progress", "Em andamento"
        COMPLETED = "completed", "Concluído"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    legal_name = models.CharField(max_length=200, blank=True)
    organization_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INDIVIDUAL,
        db_index=True,
    )
    document = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=24, blank=True)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organizations",
    )
    onboarding_status = models.CharField(
        max_length=20,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.PENDING,
        db_index=True,
    )
    onboarding_step = models.PositiveSmallIntegerField(default=1)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"], name="org_slug_idx"),
            models.Index(fields=["status"], name="org_status_idx"),
            models.Index(fields=["created_by"], name="org_created_by_idx"),
            models.Index(fields=["created_at"], name="org_created_at_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def accepts_operational_writes(self) -> bool:
        return self.status == self.Status.ACTIVE
