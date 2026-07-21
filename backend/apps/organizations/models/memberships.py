"""Memberships e papéis por organização."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class OrganizationMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Proprietário"
        ADMIN = "admin", "Administrador"
        THERAPIST = "therapist", "Terapeuta"
        RECEPTIONIST = "receptionist", "Recepcionista"
        FINANCE = "finance", "Financeiro"
        VIEWER = "viewer", "Somente leitura"

    class Status(models.TextChoices):
        INVITED = "invited", "Convidado"
        ACTIVE = "active", "Ativo"
        SUSPENDED = "suspended", "Suspenso"
        REVOKED = "revoked", "Revogado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    is_default = models.BooleanField(default=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="organization_memberships_invited",
        null=True,
        blank=True,
    )
    joined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization__name", "user__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="org_membership_unique_user",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="org_membership_one_default",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organization", "status"],
                name="org_member_org_status_idx",
            ),
            models.Index(
                fields=["user", "status"],
                name="org_member_user_status_idx",
            ),
            models.Index(
                fields=["organization", "role"],
                name="org_member_org_role_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} em {self.organization_id} ({self.role})"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE
