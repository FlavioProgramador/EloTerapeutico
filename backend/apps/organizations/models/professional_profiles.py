"""Perfil profissional específico de uma membership."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from .memberships import OrganizationMembership


class ProfessionalProfile(models.Model):
    membership = models.OneToOneField(
        OrganizationMembership,
        on_delete=models.CASCADE,
        related_name="professional_profile",
    )
    display_name = models.CharField(max_length=160, blank=True)
    professional_title = models.CharField(max_length=120, blank=True)
    council_type = models.CharField(max_length=40, blank=True)
    council_number = models.CharField(max_length=40, blank=True)
    council_region = models.CharField(max_length=20, blank=True)
    specialties = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=24, blank=True)
    public_email = models.EmailField(blank=True)
    default_appointment_duration = models.PositiveSmallIntegerField(default=50)
    default_session_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    accepts_online = models.BooleanField(default=False)
    accepts_in_person = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["membership__user__full_name"]

    def clean(self):
        super().clean()
        if self.default_appointment_duration < 5:
            raise ValidationError(
                {"default_appointment_duration": "A duração mínima é de 5 minutos."}
            )
        if self.default_session_value < 0:
            raise ValidationError(
                {"default_session_value": "O valor da sessão não pode ser negativo."}
            )
        if self.specialties is None:
            self.specialties = []
        if not isinstance(self.specialties, list):
            raise ValidationError({"specialties": "Especialidades devem ser uma lista."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name or self.membership.user.full_name
