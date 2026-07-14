"""Modelo de transações financeiras."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FinancialTransaction(models.Model):
    """Receita ou despesa pertencente a um terapeuta."""

    class TransactionType(models.TextChoices):
        INCOME = "income", _("Receita")
        EXPENSE = "expense", _("Despesa")

    class Category(models.TextChoices):
        SESSION = "session", _("Sessão")
        SUBSCRIPTION = "subscription", _("Mensalidade")
        MATERIAL = "material", _("Material")
        RENT = "rent", _("Aluguel")
        UTILITIES = "utilities", _("Contas de consumo")
        TAXES = "taxes", _("Impostos")
        SOFTWARE = "software", _("Software")
        MARKETING = "marketing", _("Marketing")
        SERVICES = "services", _("Serviços")
        REFUND = "refund", _("Reembolso")
        OTHER = "other", _("Outro")

    class PaymentMethod(models.TextChoices):
        UNINFORMED = "uninformed", _("Não informado")
        PIX = "pix", _("PIX")
        CREDIT_CARD = "credit_card", _("Cartão de Crédito")
        DEBIT_CARD = "debit_card", _("Cartão de Débito")
        CASH = "cash", _("Dinheiro")
        BANK_TRANSFER = "bank_transfer", _("Transferência Bancária")
        BOLETO = "boleto", _("Boleto")
        PAYMENT_LINK = "payment_link", _("Link de pagamento")
        OTHER = "other", _("Outro")

    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Pago")
        PARTIAL = "partial", _("Parcialmente pago")
        PENDING = "pending", _("Pendente")
        CANCELLED = "cancelled", _("Cancelado")
        REFUNDED = "refunded", _("Estornado")

    class Source(models.TextChoices):
        MANUAL = "manual", _("Manual")
        APPOINTMENT = "appointment", _("Sessão")
        SUBSCRIPTION = "subscription", _("Mensalidade")
        RECURRENCE = "recurrence", _("Recorrência")

    class RecurrenceFrequency(models.TextChoices):
        WEEKLY = "weekly", _("Semanal")
        BIWEEKLY = "biweekly", _("Quinzenal")
        MONTHLY = "monthly", _("Mensal")
        QUARTERLY = "quarterly", _("Trimestral")
        SEMIANNUAL = "semiannual", _("Semestral")
        ANNUAL = "annual", _("Anual")

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="financial_transactions",
        verbose_name=_("Terapeuta"),
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_transactions",
        verbose_name=_("Paciente"),
    )
    appointment = models.ForeignKey(
        "agenda.Appointment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_transactions",
        verbose_name=_("Consulta"),
    )
    subscription = models.ForeignKey(
        "financeiro.MonthlySubscription",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="charges",
        verbose_name=_("Mensalidade"),
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        default=TransactionType.INCOME,
        verbose_name=_("Tipo"),
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SESSION,
        verbose_name=_("Categoria"),
    )
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
        verbose_name=_("Origem"),
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Valor"))
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name=_("Valor pago"),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.UNINFORMED,
        verbose_name=_("Método de pagamento"),
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("Status"),
    )

    due_date = models.DateField(null=True, blank=True, verbose_name=_("Vencimento"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Pago em"))

    description = models.TextField(blank=True, verbose_name=_("Descrição"))
    beneficiary = models.CharField(max_length=180, blank=True, verbose_name=_("Beneficiário"))
    payment_link = models.URLField(blank=True, verbose_name=_("Link de pagamento"))
    receipt_url = models.URLField(blank=True, verbose_name=_("URL do recibo"))

    is_recurring = models.BooleanField(default=False, verbose_name=_("Recorrente"))
    recurrence_frequency = models.CharField(
        max_length=20,
        choices=RecurrenceFrequency.choices,
        blank=True,
        verbose_name=_("Frequência da recorrência"),
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Fim da recorrência"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Transação Financeira")
        verbose_name_plural = _("Transações Financeiras")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["therapist", "payment_status"], name="fin_therapist_status_idx"),
            models.Index(fields=["therapist", "created_at"], name="fin_therapist_created_idx"),
            models.Index(fields=["therapist", "due_date"], name="fin_therapist_due_idx"),
            models.Index(fields=["therapist", "transaction_type", "due_date"], name="fin_type_due_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="fin_amount_positive"),
            models.CheckConstraint(condition=Q(paid_amount__gte=0), name="fin_paid_amount_non_negative"),
            models.CheckConstraint(condition=Q(paid_amount__lte=models.F("amount")), name="fin_paid_amount_lte_amount"),
            models.UniqueConstraint(
                fields=["appointment"],
                condition=Q(appointment__isnull=False, source="appointment"),
                name="fin_unique_appointment_source",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_transaction_type_display()} – R$ {self.amount:.2f}"

    @property
    def is_overdue(self) -> bool:
        return bool(
            self.payment_status in {self.PaymentStatus.PENDING, self.PaymentStatus.PARTIAL}
            and self.due_date
            and self.due_date < timezone.localdate()
        )

    @property
    def outstanding_amount(self) -> Decimal:
        return max(self.amount - self.paid_amount, Decimal("0.00"))

    def clean(self) -> None:
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": _("O valor deve ser maior que zero.")})
        if self.paid_amount is not None and self.amount is not None and self.paid_amount > self.amount:
            raise ValidationError({"paid_amount": _("O valor pago não pode exceder o valor da transação.")})
        if self.is_recurring and not self.recurrence_frequency:
            raise ValidationError({"recurrence_frequency": _("Informe a frequência da recorrência.")})

    def can_pay(self) -> bool:
        return self.payment_status in {self.PaymentStatus.PENDING, self.PaymentStatus.PARTIAL}

    def can_cancel(self) -> bool:
        return self.payment_status in {self.PaymentStatus.PENDING, self.PaymentStatus.PARTIAL}

    def can_refund(self) -> bool:
        return self.payment_status == self.PaymentStatus.PAID

    def pay(self, payment_method: str = PaymentMethod.PIX, paid_at=None, amount: Decimal | None = None) -> None:
        if not self.can_pay():
            raise ValidationError(_("Esta transação não está pendente de pagamento."))
        paid_value = amount if amount is not None else self.outstanding_amount
        if paid_value <= 0 or paid_value > self.outstanding_amount:
            raise ValidationError(_("Valor de pagamento inválido."))
        self.paid_amount += paid_value
        self.payment_method = payment_method
        self.paid_at = paid_at or timezone.now()
        self.payment_status = self.PaymentStatus.PAID if self.paid_amount == self.amount else self.PaymentStatus.PARTIAL
        self.save(
            update_fields=[
                "paid_amount",
                "payment_method",
                "paid_at",
                "payment_status",
                "updated_at",
            ]
        )

        if self.appointment and self.payment_status == self.PaymentStatus.PAID:
            appointment = self.appointment
            if appointment.status == appointment.Status.SCHEDULED:
                appointment.status = appointment.Status.CONFIRMED
                appointment.save(update_fields=["status", "updated_at"])

    def cancel(self) -> None:
        if not self.can_cancel():
            raise ValidationError(_("Apenas transações pendentes podem ser canceladas."))
        self.payment_status = self.PaymentStatus.CANCELLED
        self.save(update_fields=["payment_status", "updated_at"])

    def refund(self) -> None:
        if not self.can_refund():
            raise ValidationError(_("Apenas transações pagas podem ser estornadas."))
        self.payment_status = self.PaymentStatus.REFUNDED
        self.save(update_fields=["payment_status", "updated_at"])

    @classmethod
    def monthly_summary(cls, therapist, year: int, month: int) -> dict:
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
        queryset = cls.objects.filter(therapist=therapist, due_date__range=(start, end))
        paid = queryset.filter(payment_status=cls.PaymentStatus.PAID)
        income = paid.filter(transaction_type=cls.TransactionType.INCOME).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        expense = paid.filter(transaction_type=cls.TransactionType.EXPENSE).aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0.00")
        pending = queryset.filter(payment_status__in=[cls.PaymentStatus.PENDING, cls.PaymentStatus.PARTIAL]).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")
        return {
            "year": year,
            "month": month,
            "total_income": income,
            "total_expense": expense,
            "balance": income - expense,
            "total_pending": pending,
            "transaction_count": queryset.count(),
        }
