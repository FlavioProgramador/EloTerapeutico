"""Modelo principal de pacientes."""

from django.conf import settings
from django.db import models

from core.validators import validate_cpf, validate_phone

from .choices import (
    PatientAttendanceType,
    PatientGender,
    PatientMaritalStatus,
    PatientModality,
    PatientPayerType,
    PatientPlannedFrequency,
    PatientReminderRecipient,
    PatientStatus,
)
from .managers import AllPatientsManager, PatientManager
from .mixins import PatientComputedPropertiesMixin, PatientLifecycleMixin
from .paths import patient_photo_path


class Patient(PatientComputedPropertiesMixin, PatientLifecycleMixin, models.Model):
    Gender = PatientGender
    Status = PatientStatus
    MaritalStatus = PatientMaritalStatus
    AttendanceType = PatientAttendanceType
    Modality = PatientModality
    PayerType = PatientPayerType
    PlannedFrequency = PatientPlannedFrequency
    ReminderRecipient = PatientReminderRecipient

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
