"""Mixins comportamentais do modelo de paciente."""

import re
from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone


class PatientComputedPropertiesMixin:
    """Propriedades calculadas e mascaramento de dados sensíveis."""

    @property
    def display_name(self) -> str:
        return self.social_name or self.full_name

    @property
    def age(self) -> int | None:
        if not self.birth_date:
            return None
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    @property
    def is_minor(self) -> bool:
        age = self.age
        return age is not None and age < 18

    @property
    def formatted_cpf(self) -> str:
        if self.cpf and len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return ""

    @property
    def masked_cpf(self) -> str:
        if self.cpf and len(self.cpf) == 11:
            return f"{self.cpf[:3]}.***.***-{self.cpf[-2:]}"
        return "CPF não informado"


class PatientLifecycleMixin:
    """Normalização, validação e ciclo de vida administrativo do paciente."""

    def clean(self):
        if self.cpf:
            self.cpf = re.sub(r"\D", "", self.cpf)
        if self.guardian_cpf:
            self.guardian_cpf = re.sub(r"\D", "", self.guardian_cpf)
        if self.financial_responsible_cpf:
            self.financial_responsible_cpf = re.sub(
                r"\D",
                "",
                self.financial_responsible_cpf,
            )
        if self.is_minor and not self.guardian_name:
            raise ValidationError(
                {"guardian_name": "Pacientes menores de 18 anos devem ter responsável legal cadastrado."}
            )
        if self.payer_type == self.PayerType.INSURANCE and not self.insurance_name:
            raise ValidationError({"insurance_name": "Informe o convênio do paciente."})

    def save(self, *args, **kwargs):
        if self.cpf:
            self.cpf = re.sub(r"\D", "", self.cpf)
        else:
            self.cpf = None
        if self.guardian_cpf:
            self.guardian_cpf = re.sub(r"\D", "", self.guardian_cpf)
        if self.financial_responsible_cpf:
            self.financial_responsible_cpf = re.sub(
                r"\D",
                "",
                self.financial_responsible_cpf,
            )
        if self.consent_terms_accepted and not self.consent_at:
            self.consent_at = timezone.now()
        if not self.consent_terms_accepted:
            self.consent_at = None
        super().save(*args, **kwargs)

    def soft_delete(self) -> None:
        self.deleted_at = timezone.now()
        self.is_active = False
        self.status = self.Status.ARCHIVED
        self.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])

    def deactivate(self) -> None:
        self.is_active = False
        self.status = self.Status.INACTIVE
        self.save(update_fields=["is_active", "status", "updated_at"])

    def activate(self) -> None:
        self.deleted_at = None
        self.is_active = True
        self.status = self.Status.ACTIVE
        self.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])

    def restore(self) -> None:
        self.activate()
