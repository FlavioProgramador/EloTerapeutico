"""Convites seguros de membros para organizações."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .memberships import OrganizationMembership


class OrganizationInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACCEPTED = "accepted", "Aceito"
        REVOKED = "revoked", "Revogado"
        EXPIRED = "expired", "Expirado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=OrganizationMembership.Role.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField(db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="organization_invitations_sent",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="organization_invitations_accepted",
        null=True,
        blank=True,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                condition=Q(status="pending"),
                name="org_invite_unique_pending_email",
            )
        ]
        indexes = [
            models.Index(
                fields=["organization", "status"],
                name="org_invite_org_status_idx",
            ),
            models.Index(fields=["email", "status"], name="org_invite_email_status_idx"),
        ]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Convite {self.email} para {self.organization_id}"
