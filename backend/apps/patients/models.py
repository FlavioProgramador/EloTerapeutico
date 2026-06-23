"""
apps/patients/models.py
Modelo de Paciente para o sistema Elo Terapêutico.

Implementa:
- Soft delete (deleted_at / is_active)
- Validação de CPF e telefone via core/validators
- Endereço como JSONField estruturado
- Cálculo de idade como property
- Gerenciamento de responsável para pacientes menores
"""

import re
from datetime import date

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.validators import validate_cpf, validate_phone


class PatientManager(models.Manager):
    """
    Manager padrão que exclui pacientes com soft delete aplicado.
    Retorna apenas pacientes com is_active=True (deleted_at=None).
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllPatientsManager(models.Manager):
    """
    Manager alternativo que retorna TODOS os pacientes,
    incluindo os que foram excluídos via soft delete.
    Útil para o Django Admin e relatórios administrativos.
    """

    def get_queryset(self):
        return super().get_queryset()


class Patient(models.Model):
    """
    Representa um paciente cadastrado no sistema.

    Regras de negócio:
    - CPF é armazenado somente com dígitos (11 caracteres), sem formatação.
    - Soft delete: ao invés de excluir o registro, seta deleted_at e is_active=False.
    - Terapeutas só acessam seus próprios pacientes (filtrado na view).
    - Pacientes menores de 18 anos devem ter guardian_name e guardian_cpf preenchidos.
    """

    # ── Escolhas de gênero ───────────────────────────────────────────────────
    class Gender(models.TextChoices):
        MALE = "M", "Masculino"
        FEMALE = "F", "Feminino"
        OTHER = "O", "Outro"
        PREFER_NOT_TO_SAY = "N", "Prefiro não informar"

    # ── Escolhas de status do paciente ───────────────────────────────────────
    class Status(models.TextChoices):
        ACTIVE = "ativo", "Ativo"
        INACTIVE = "inativo", "Inativo"
        DISCHARGED = "alta", "Alta"

    # ── Identificação pessoal ────────────────────────────────────────────────
    full_name = models.CharField(
        max_length=255,
        verbose_name="Nome completo",
        db_index=True,
    )
    cpf = models.CharField(
        max_length=11,
        unique=True,
        validators=[validate_cpf],
        verbose_name="CPF",
        help_text="Somente dígitos (11 caracteres). Aceita formato com pontos/traços no input.",
    )
    birth_date = models.DateField(
        verbose_name="Data de nascimento",
    )
    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        default=Gender.PREFER_NOT_TO_SAY,
        verbose_name="Gênero",
    )

    # ── Contato ──────────────────────────────────────────────────────────────
    email = models.EmailField(
        blank=True,
        verbose_name="E-mail",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone",
        help_text="Formato: (11) 99999-9999",
    )

    # ── Endereço (estruturado como JSON) ─────────────────────────────────────
    address = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Endereço",
        help_text=(
            "Estrutura esperada: {"
            '"cep": "01310-100", '
            '"street": "Av. Paulista", '
            '"number": "1000", '
            '"complement": "Apto 42", '
            '"neighborhood": "Bela Vista", '
            '"city": "São Paulo", '
            '"state": "SP"}'
        ),
    )

    # ── Vínculo com terapeuta ────────────────────────────────────────────────
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patients",
        verbose_name="Terapeuta responsável",
        limit_choices_to={"role": "therapist"},
    )

    # ── Status do atendimento ────────────────────────────────────────────────
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Status",
        db_index=True,
    )

    # ── Informações complementares ───────────────────────────────────────────
    referral_source = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Origem / Indicação",
        help_text="Como o paciente conheceu o terapeuta (ex: indicação, redes sociais, plano de saúde).",
    )

    # ── Responsável legal (para pacientes menores de 18 anos) ────────────────
    guardian_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nome do responsável",
        help_text="Preencher para pacientes menores de 18 anos.",
    )
    guardian_cpf = models.CharField(
        max_length=11,
        blank=True,
        validators=[validate_cpf],
        verbose_name="CPF do responsável",
        help_text="Somente dígitos. Preencher para pacientes menores de 18 anos.",
    )

    # ── Observações gerais (não clínicas) ────────────────────────────────────
    notes = models.TextField(
        blank=True,
        verbose_name="Observações gerais",
        help_text=(
            "Campo para anotações administrativas não clínicas. "
            "Informações clínicas devem ser registradas no Prontuário."
        ),
    )

    # ── Controle de soft delete ──────────────────────────────────────────────
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
        help_text="Desmarcado via soft delete. Não edite manualmente.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Excluído em",
        help_text="Preenchido automaticamente ao realizar soft delete.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    # ── Managers ─────────────────────────────────────────────────────────────
    objects = PatientManager()         # Padrão: exclui soft-deleted
    all_objects = AllPatientsManager() # Retorna todos, inclusive deletados

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ["full_name"]
        indexes = [
            models.Index(fields=["therapist"], name="patient_therapist_idx"),
            models.Index(fields=["cpf"], name="patient_cpf_idx"),
            models.Index(fields=["status"], name="patient_status_idx"),
            models.Index(fields=["deleted_at"], name="patient_deleted_at_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} (CPF: {self.formatted_cpf})"

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def age(self) -> int | None:
        """
        Calcula a idade atual do paciente em anos completos.
        Retorna None se birth_date não estiver definido.
        """
        if not self.birth_date:
            return None
        today = date.today()
        birthday_this_year = self.birth_date.replace(year=today.year)
        # Verifica se o aniversário já ocorreu neste ano
        years = today.year - self.birth_date.year
        if birthday_this_year > today:
            years -= 1
        return years

    @property
    def is_minor(self) -> bool:
        """Retorna True se o paciente é menor de 18 anos."""
        age = self.age
        return age is not None and age < 18

    @property
    def formatted_cpf(self) -> str:
        """Retorna o CPF formatado com pontos e traço (XXX.XXX.XXX-XX)."""
        if len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf

    # ── Métodos de ciclo de vida ──────────────────────────────────────────────

    def clean(self):
        """
        Validações de nível de modelo executadas antes de salvar.
        - Remove a formatação do CPF antes de persistir.
        - Remove a formatação do CPF do responsável.
        - Verifica se menor tem responsável cadastrado.
        """
        from django.core.exceptions import ValidationError

        # Normaliza CPF: armazena somente dígitos
        if self.cpf:
            self.cpf = re.sub(r"\D", "", self.cpf)

        # Normaliza CPF do responsável
        if self.guardian_cpf:
            self.guardian_cpf = re.sub(r"\D", "", self.guardian_cpf)

        # Valida responsável para menores
        if self.is_minor and not self.guardian_name:
            raise ValidationError(
                {"guardian_name": "Pacientes menores de 18 anos devem ter um responsável cadastrado."}
            )

    def save(self, *args, **kwargs):
        """
        Sobrescreve save para garantir que o CPF seja sempre
        persistido somente com dígitos, independente do input.
        """
        if self.cpf:
            self.cpf = re.sub(r"\D", "", self.cpf)
        if self.guardian_cpf:
            self.guardian_cpf = re.sub(r"\D", "", self.guardian_cpf)
        super().save(*args, **kwargs)

    def soft_delete(self) -> None:
        """
        Realiza soft delete do paciente:
        - Seta deleted_at com o timestamp atual
        - Marca is_active=False
        - Atualiza status para 'inativo'

        O paciente NÃO é removido do banco de dados,
        apenas ocultado das consultas padrão.
        """
        self.deleted_at = timezone.now()
        self.is_active = False
        self.status = self.Status.INACTIVE
        self.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])

    def restore(self) -> None:
        """
        Restaura um paciente que foi removido via soft delete:
        - Limpa deleted_at
        - Marca is_active=True
        - Restaura status para 'ativo'
        """
        self.deleted_at = None
        self.is_active = True
        self.status = self.Status.ACTIVE
        self.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])
