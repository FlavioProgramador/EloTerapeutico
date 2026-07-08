"""
apps/users/models.py
Modelo de usuário customizado para terapeutas, secretárias e administradores.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from core.validators import validate_crp, validate_phone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Usuário do sistema. O identificador principal é o e-mail.
    Suporta três papéis: Terapeuta, Secretária e Administrador de Clínica.
    """

    class Role(models.TextChoices):
        THERAPIST = "therapist", "Terapeuta"
        SECRETARY = "secretary", "Secretária"
        ADMIN = "admin", "Administrador"

    # ── Identificação ───────────────────────────────────────────────────────
    email = models.EmailField(unique=True, verbose_name="E-mail")
    full_name = models.CharField(max_length=255, verbose_name="Nome completo")

    # ── Perfil profissional ─────────────────────────────────────────────────
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.THERAPIST,
        verbose_name="Papel no sistema",
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Especialidade",
        help_text="Ex: Psicologia Cognitivo-Comportamental, Fonoaudiologia...",
    )
    crp_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_crp],
        verbose_name="Número do CRP",
        help_text="Formato: XX/XXXXXX (ex: 06/123456)",
    )
    bio = models.TextField(blank=True, verbose_name="Apresentação / Bio")
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone],
        verbose_name="Telefone",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Foto de perfil",
    )

    # ── Configurações de agenda ─────────────────────────────────────────────
    default_session_duration = models.PositiveIntegerField(
        default=50,
        verbose_name="Duração padrão da sessão (min)",
    )
    default_session_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name="Valor padrão da sessão (R$)",
    )

    # ── Controle de conta ───────────────────────────────────────────────────
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Data de cadastro")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Último login")

    # Contador de tentativas de login para bloqueio de conta
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_therapist(self) -> bool:
        return self.role == self.Role.THERAPIST

    @property
    def is_secretary(self) -> bool:
        return self.role == self.Role.SECRETARY

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def lock_account(self, minutes: int = 30) -> None:
        """Bloqueia a conta por X minutos após tentativas falhas consecutivas."""
        from datetime import timedelta

        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=["locked_until"])

    def is_locked(self) -> bool:
        """Retorna True se a conta está bloqueada no momento."""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def reset_login_attempts(self) -> None:
        """Reseta o contador de tentativas após login bem-sucedido."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=["failed_login_attempts", "locked_until"])


class WorkingHours(models.Model):
    """Horários de atendimento configurados pelo terapeuta para cada dia da semana."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Segunda-feira"
        TUESDAY = 1, "Terça-feira"
        WEDNESDAY = 2, "Quarta-feira"
        THURSDAY = 3, "Quinta-feira"
        FRIDAY = 4, "Sexta-feira"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    therapist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="working_hours",
        verbose_name="Terapeuta",
    )
    weekday = models.IntegerField(choices=Weekday.choices, verbose_name="Dia da semana")
    start_time = models.TimeField(verbose_name="Início do atendimento")
    end_time = models.TimeField(verbose_name="Fim do atendimento")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Horário de Atendimento"
        verbose_name_plural = "Horários de Atendimento"
        unique_together = ("therapist", "weekday")
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.therapist.full_name} – {self.get_weekday_display()} {self.start_time}–{self.end_time}"
