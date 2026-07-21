"""Base abstrata para entidades clínicas pertencentes a uma organização."""

from django.core.exceptions import ValidationError
from django.db import models


class ClinicalTenantModel(models.Model):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_items",
        db_index=True,
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        patient = getattr(self, "patient", None) if getattr(self, "patient_id", None) else None
        if patient is not None and patient.organization_id != self.organization_id:
            raise ValidationError({"patient": "O paciente pertence a outra organização."})
        appointment = (
            getattr(self, "appointment", None)
            if getattr(self, "appointment_id", None)
            else None
        )
        if appointment is not None and appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})
