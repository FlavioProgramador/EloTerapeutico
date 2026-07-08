"""Modelo principal de pacientes."""

import re
from datetime import date
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.validators import validate_cpf, validate_phone

from .managers import AllPatientsManager, PatientManager


def patient_photo_path(instance, filename: str) -> str:
    """Gera nome não previsível sem expor o nome do paciente no storage."""

    suffix = Path(filename).suffix.lower()
    owner = instance.therapist_id or "unassigned"
    return f"patient_photos/{owner}/{uuid4().hex}{suffix}"


# Mantém o caminho serializado em migrations antigas mesmo após mover o código.
patient_photo_path.__module__ = "apps.patients.models"


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Masculino"
        FEMALE = "F", "Feminino"
        OTHER = "O", "Outro"
        PREFER_NOT_TO_SAY = "N", "Prefiro não informar"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        EVALUATION = "evaluation", "Em avaliação"
        WAITING_RETURN = "waiting_return", "Aguardando retorno"
        DISCHARGED = "discharged", "Alta"
        INACTIVE = "inactive", "Encerrado"
        ARCHIVED = "archived", "Arquivado"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "Solteiro(a)"
        MARRIED = "married", "Casado(a)"
        DIVORCED = "divorced", "Divorciado(a)"
        WIDOWED = "widowed", "Viúvo(a)"
        OTHER = "other", "Outro"

    class AttendanceType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        COUPLE = "couple", "Casal"
        FAMILY = "family", "Familiar"
        GROUP = "group", "Grupo"
        OTHER = "other", "Outro"

    class Modality(models.TextChoices):
        IN_PERSON = "in_person", "Presencial"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Híbrido"

    class PayerType(models.TextChoices):
        PRIVATE = "private", "Particular"
        INSURANCE = "insurance", "Convênio"

    class PlannedFrequency(models.TextChoices):
        WEEKLY = "weekly", "Semanal"
        BIWEEKLY = "biweekly", "Quinzenal"
        MONTHLY = "monthly", "Mensal"
        AS_NEEDED = "as_needed", "Conforme necessidade"

    class ReminderRecipient(models.TextChoices):
        PATIENT = "patient", "Paciente"
        FINANCIAL_RESPONSIBLE = "financial_responsible", "Responsável financeiro"
        BOTH = "both", "Paciente e responsável"
        NONE = "none", "Não enviar"

    full_name = models.CharField(max_length=255, db_index=True, verbose_name="Nome completo")
    social_name = models.CharField(max_length=255, blank=True, verbose_name="Nome social")
    photo = models.FileField(
        upload_to=patient_photo_path,
        null=True,
        blank=True,
        verbose_name="Foto do paciente",
    )
    cpf = models.CharField(
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_cpf],
        verbose_name="CPF",
    )
    rg = models.CharField(max_length=30, blank=True, verbose_name="RG")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de nascimento")
    treatment_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Início dos atendimentos",
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.PREFER_NOT_TO_SAY,
        verbose_name="Gênero",
    )
    marital_status = models.CharField(
        max_length=16,
        choices=MaritalStatus.choices,
        blank=True,
        verbose_name="Estado civil",
    )
    profession = models.CharField(max_length=160, blank=True, verbose_name="Profissão")
    social_network = models.CharField(max_length=160, blank=True, verbose_name="Rede social")

    email = models.EmailField(blank=True, verbose_name="E-mail")
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone",
    )
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="WhatsApp",
    )
    address = models.JSONField(default=dict, blank=True, verbose_name="Endereço")

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients",
        verbose_name="Terapeuta responsável",
        limit_choices_to={"role": "therapist"},
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status",
        db_index=True,
    )
    attendance_type = models.CharField(
        max_length=20,
        choices=AttendanceType.choices,
        default=AttendanceType.INDIVIDUAL,
        verbose_name="Tipo de atendimento",
    )
    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.IN_PERSON,
        verbose_name="Modalidade",
    )
    payer_type = models.CharField(
        max_length=20,
        choices=PayerType.choices,
        default=PayerType.PRIVATE,
        verbose_name="Forma de atendimento",
    )
    insurance_name = models.CharField(max_length=120, blank=True, verbose_name="Convênio")
    session_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Valor de referência da sessão",
    )
    planned_frequency = models.CharField(
        max_length=20,
        choices=PlannedFrequency.choices,
        blank=True,
        verbose_name="Frequência planejada",
    )
    reminders_enabled = models.BooleanField(default=True, verbose_name="Lembretes ativos")
    reminder_recipient = models.CharField(
        max_length=32,
        choices=ReminderRecipient.choices,
        default=ReminderRecipient.PATIENT,
        verbose_name="Destinatário dos lembretes",
    )

    referral_source = models.CharField(max_length=255, blank=True, verbose_name="Origem / indicação")
    tags = models.JSONField(default=list, blank=True, verbose_name="Etiquetas")

    emergency_contact_name = models.CharField(max_length=255, blank=True, verbose_name="Contato de emergência")
    emergency_contact_relationship = models.CharField(max_length=80, blank=True, verbose_name="Relação do contato")
    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone de emergência",
    )

    guardian_name = models.CharField(max_length=255, blank=True, verbose_name="Nome do responsável legal")
    guardian_cpf = models.CharField(
        max_length=11,
        blank=True,
        validators=[validate_cpf],
        verbose_name="CPF do responsável legal",
    )
    guardian_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone do responsável legal",
    )
    guardian_email = models.EmailField(blank=True, verbose_name="E-mail do responsável legal")
    guardian_relationship = models.CharField(max_length=80, blank=True, verbose_name="Relação do responsável legal")

    financial_responsible_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Responsável financeiro",
    )
    financial_responsible_cpf = models.CharField(
        max_length=11,
        blank=True,
        validators=[validate_cpf],
        verbose_name="CPF do responsável financeiro",
    )
    financial_responsible_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone do responsável financeiro",
    )
    financial_responsible_email = models.EmailField(
        blank=True,
        verbose_name="E-mail do responsável financeiro",
    )
    financial_responsible_marital_status = models.CharField(
        max_length=16,
        choices=MaritalStatus.choices,
        blank=True,
        verbose_name="Estado civil do responsável financeiro",
    )
    financial_responsible_naturality = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Naturalidade do responsável financeiro",
    )
    financial_responsible_occupation = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="Ocupação do responsável financeiro",
    )
    financial_responsible_relationship = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="Relação do responsável financeiro",
    )

    consent_terms_accepted = models.BooleanField(default=False, verbose_name="Consentimentos registrados")
    consent_at = models.DateTimeField(null=True, blank=True, verbose_name="Consentimento registrado em")
    notes = models.TextField(blank=True, verbose_name="Observações administrativas")

    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Arquivado em")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = PatientManager()
    all_objects = AllPatientsManager()

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["therapist"], name="patient_therapist_idx"),
            models.Index(fields=["cpf"], name="patient_cpf_idx"),
            models.Index(fields=["status"], name="patient_status_idx"),
            models.Index(fields=["deleted_at"], name="patient_deleted_at_idx"),
            models.Index(fields=["therapist", "status"], name="patient_owner_status_idx"),
            models.Index(fields=["created_at"], name="patient_created_at_idx"),
            models.Index(fields=["birth_date"], name="patient_birth_date_idx"),
            models.Index(fields=["payer_type", "insurance_name"], name="patient_payer_insurance_idx"),
        ]

    def __str__(self) -> str:
        return f"Paciente #{self.pk}"

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
