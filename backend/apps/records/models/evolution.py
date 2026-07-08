"""Modelo de evolução de sessão."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField


class Evolution(models.Model):
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
        help_text="Consulta da agenda que originou esta evolução (opcional).",
    )
    content = EncryptedTextField(
        verbose_name="Conteúdo da sessão",
        help_text="Texto descritivo da sessão terapêutica.",
    )
    cid10 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="CID-10",
        help_text="Código CID-10 associado à sessão (ex: F41.1).",
    )
    session_date = models.DateField(
        verbose_name="Data da sessão",
        help_text="Data em que a sessão terapêutica ocorreu.",
    )
    is_locked = models.BooleanField(
        default=False,
        verbose_name="Bloqueada",
        help_text=(
            "Evoluções bloqueadas não podem ser editadas. Só aceitam aditivos."
        ),
    )
    locked_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Bloqueada em",
        help_text="Data/hora em que a evolução foi bloqueada.",
    )
    is_confidential = models.BooleanField(
        default=False,
        verbose_name="Confidencial",
        help_text=(
            "Marcar como confidencial. Informações visíveis apenas para o autor "
            "ou com permissão especial."
        ),
    )
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
