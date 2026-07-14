"""Choices do domínio de pacientes."""

from django.db import models


class PatientGender(models.TextChoices):
    MALE = "M", "Masculino"
    FEMALE = "F", "Feminino"
    OTHER = "O", "Outro"
    PREFER_NOT_TO_SAY = "N", "Prefiro não informar"


class PatientStatus(models.TextChoices):
    ACTIVE = "active", "Ativo"
    EVALUATION = "evaluation", "Em avaliação"
    WAITING_RETURN = "waiting_return", "Aguardando retorno"
    DISCHARGED = "discharged", "Alta"
    INACTIVE = "inactive", "Encerrado"
    ARCHIVED = "archived", "Arquivado"


class PatientMaritalStatus(models.TextChoices):
    SINGLE = "single", "Solteiro(a)"
    MARRIED = "married", "Casado(a)"
    DIVORCED = "divorced", "Divorciado(a)"
    WIDOWED = "widowed", "Viúvo(a)"
    OTHER = "other", "Outro"


class PatientAttendanceType(models.TextChoices):
    INDIVIDUAL = "individual", "Individual"
    COUPLE = "couple", "Casal"
    FAMILY = "family", "Familiar"
    GROUP = "group", "Grupo"
    OTHER = "other", "Outro"


class PatientModality(models.TextChoices):
    IN_PERSON = "in_person", "Presencial"
    ONLINE = "online", "Online"
    HYBRID = "hybrid", "Híbrido"


class PatientPayerType(models.TextChoices):
    PRIVATE = "private", "Particular"
    INSURANCE = "insurance", "Convênio"


class PatientPlannedFrequency(models.TextChoices):
    WEEKLY = "weekly", "Semanal"
    BIWEEKLY = "biweekly", "Quinzenal"
    MONTHLY = "monthly", "Mensal"
    AS_NEEDED = "as_needed", "Conforme necessidade"


class PatientReminderRecipient(models.TextChoices):
    PATIENT = "patient", "Paciente"
    FINANCIAL_RESPONSIBLE = "financial_responsible", "Responsável financeiro"
    BOTH = "both", "Paciente e responsável"
    NONE = "none", "Não enviar"
