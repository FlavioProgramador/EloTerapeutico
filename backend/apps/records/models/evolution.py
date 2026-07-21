"""Modelo de evolução de sessão."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField

from .tenant import ClinicalTenantModel


class Evolution(ClinicalTenantModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="records_evolution_items",
        db_index=True,
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="evolutions",
        verbose_name="Paciente",
    )
    appointment = models.OneToOneField(
        "agenda.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evolution",
        verbose_name="Agendamento vinculado",
    )
    content = EncryptedTextField(verbose_name="Conteúdo da sessão")
    cid10 = models.CharField(max_length=10, blank=True, verbose_name="CID-10")
    session_date = models.DateField(verbose_name="Data da sessão")
    is_locked = models.BooleanField(default=False, verbose_name="Bloqueada")
    locked_at = models.DateTimeField(null=True, blank=True, verbose_name="Bloqueada em")
    is_confidential = models.BooleanField(default=False, verbose_name="Confidencial")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evolutions_created",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Evolução"
        verbose_name_plural = "Evoluções"
        ordering = ["-session_date", "-created_at"]
        permissions = [
            ("view_confidential_evolution", "Can view confidential evolution"),
            ("export_confidential_evolution", "Can export confidential evolution"),
        ]
        indexes = [
            models.Index(
                fields=["organization", "patient", "session_date"],
                name="evolution_org_patient_idx",
            ),
            models.Index(
                fields=["patient", "session_date"],
                name="evolution_patient_date_idx",
            ),
            models.Index(
                fields=["is_locked", "created_at"],
                name="evolution_lock_check_idx",
            ),
        ]

    def __str__(self):
        return f"Evolução {self.patient} – {self.session_date:%d/%m/%Y}"

    def can_be_edited(self) -> bool:
        if self.is_locked:
            return False
        if self.created_at is None:
            return True
        return timezone.now() < self.created_at + timedelta(hours=48)

    def lock(self) -> None:
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save(update_fields=["is_locked", "locked_at"])
