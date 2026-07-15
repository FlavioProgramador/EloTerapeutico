"""Entidades explícitas de clínica, membership e convite."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.validators import validate_phone


class Clinic(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        SUSPENDED = "suspended", "Suspensa"
        ARCHIVED = "archived", "Arquivada"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Identificador público",
    )
    name = models.CharField(max_length=160, verbose_name="Nome da clínica")
    legal_name = models.CharField(max_length=200, blank=True, verbose_name="Razão social")
    document = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Documento",
        help_text="Armazene somente quando houver finalidade e base legal definidas.",
    )
    email = models.EmailField(blank=True, verbose_name="E-mail")
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone",
    )
    timezone = models.CharField(
        max_length=64,
        default="America/Sao_Paulo",
        verbose_name="Fuso horário",
    )
    logo = models.ImageField(
        upload_to="clinics/logos/",
        null=True,
        blank=True,
        verbose_name="Logotipo",
    )
    address = models.JSONField(default=dict, blank=True, verbose_name="Endereço")
    settings = models.JSONField(default=dict, blank=True, verbose_name="Configurações")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"
        ordering = ["name", "id"]
        indexes = [
            models.Index(fields=["status", "name"], name="users_clinic_status_name_idx"),
        ]

    def __str__(self) -> str:
        return self.name


class ClinicMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Proprietário"
        ADMIN = "admin", "Administrador da clínica"
        THERAPIST = "therapist", "Terapeuta"
        SECRETARY = "secretary", "Secretária"
        FINANCIAL = "financial", "Financeiro"
        SUPPORT = "support", "Suporte restrito"

    class Status(models.TextChoices):
        INVITED = "invited", "Convidado"
        ACTIVE = "active", "Ativo"
        SUSPENDED = "suspended", "Suspenso"
        REVOKED = "revoked", "Revogado"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Identificador público",
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Clínica",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinic_memberships",
        verbose_name="Usuário",
    )
    role = models.CharField(max_length=20, choices=Role.choices, verbose_name="Função")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name="Status",
    )
    extra_permissions = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Permissões adicionais",
    )
    joined_at = models.DateTimeField(null=True, blank=True, verbose_name="Entrada em")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinic_memberships_invited",
        verbose_name="Convidado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Vínculo com clínica"
        verbose_name_plural = "Vínculos com clínicas"
        ordering = ["clinic__name", "user_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "user"],
                name="users_clinic_membership_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "status", "clinic"],
                name="users_clinic_member_active_idx",
            ),
            models.Index(
                fields=["clinic", "role", "status"],
                name="users_clinic_member_role_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Membership {self.public_id}"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE and self.clinic.status == Clinic.Status.ACTIVE

    def activate(self) -> None:
        self.status = self.Status.ACTIVE
        if self.joined_at is None:
            self.joined_at = timezone.now()
        self.save(update_fields=["status", "joined_at", "updated_at"])


class ClinicInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        ACCEPTED = "accepted", "Aceito"
        EXPIRED = "expired", "Expirado"
        REVOKED = "revoked", "Revogado"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Identificador público",
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name="Clínica",
    )
    email = models.EmailField(verbose_name="E-mail convidado")
    role = models.CharField(
        max_length=20,
        choices=ClinicMembership.Role.choices,
        verbose_name="Função",
    )
    token_hash = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        verbose_name="Hash do token",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Status",
    )
    expires_at = models.DateTimeField(db_index=True, verbose_name="Expira em")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clinic_invitations_sent",
        verbose_name="Convidado por",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clinic_invitations_accepted",
        verbose_name="Aceito por",
    )
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Aceito em")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Convite de clínica"
        verbose_name_plural = "Convites de clínica"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["clinic", "email", "status"],
                name="users_clinic_invite_email_status_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["clinic", "status", "expires_at"],
                name="users_clinic_invite_pending_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Convite {self.public_id}"

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= timezone.now()
