"""
apps/financeiro/models.py
Modelos de gestão financeira: transações, pagamentos e resumos mensais.
"""

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class FinancialTransaction(models.Model):
    """
    Representa uma transação financeira do terapeuta.
    Pode estar vinculada a um paciente e/ou a uma consulta específica.
    """

    # ── Tipos de transação ───────────────────────────────────────────────────
    class TransactionType(models.TextChoices):
        INCOME = "income", _("Receita")
        EXPENSE = "expense", _("Despesa")

    # ── Categorias ───────────────────────────────────────────────────────────
    class Category(models.TextChoices):
        SESSION = "session", _("Sessão")
        SUBSCRIPTION = "subscription", _("Assinatura / Plano")
        MATERIAL = "material", _("Material")
        REFUND = "refund", _("Reembolso")
        OTHER = "other", _("Outro")

    # ── Métodos de pagamento ─────────────────────────────────────────────────
    class PaymentMethod(models.TextChoices):
        PIX = "pix", _("PIX")
        CREDIT_CARD = "credit_card", _("Cartão de Crédito")
        DEBIT_CARD = "debit_card", _("Cartão de Débito")
        CASH = "cash", _("Dinheiro")
        BANK_TRANSFER = "bank_transfer", _("Transferência Bancária")
        OTHER = "other", _("Outro")

    # ── Status de pagamento ──────────────────────────────────────────────────
    class PaymentStatus(models.TextChoices):
        PAID = "paid", _("Pago")
        PENDING = "pending", _("Pendente")
        CANCELLED = "cancelled", _("Cancelado")
        REFUNDED = "refunded", _("Estornado")

    # ── Relacionamentos ──────────────────────────────────────────────────────
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

    # ── Dados da transação ───────────────────────────────────────────────────
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
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Valor (R$)"),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.PIX,
        verbose_name=_("Método de Pagamento"),
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("Status do Pagamento"),
    )

    # ── Datas ────────────────────────────────────────────────────────────────
    due_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data de Vencimento"),
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Pago em"),
    )

    # ── Informações adicionais ───────────────────────────────────────────────
    description = models.TextField(
        blank=True,
        verbose_name=_("Descrição / Observações"),
    )
    receipt_url = models.URLField(
        blank=True,
        verbose_name=_("URL do Recibo"),
        help_text=_("URL do PDF do recibo armazenado no Azure Blob Storage."),
    )

    # ── Auditoria ────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Transação Financeira")
        verbose_name_plural = _("Transações Financeiras")
        ordering = ["-created_at"]
        indexes = [
            # Índice para consultas de status por terapeuta (ex: listar pendentes)
            models.Index(
                fields=["therapist", "payment_status"],
                name="fin_therapist_status_idx",
            ),
            # Índice para consultas cronológicas por terapeuta (ex: resumo mensal)
            models.Index(
                fields=["therapist", "created_at"],
                name="fin_therapist_created_idx",
            ),
        ]

    def __str__(self) -> str:
        tipo = self.get_transaction_type_display()
        valor = f"R$ {self.amount:,.2f}"
        return f"{tipo} – {valor} ({self.get_payment_status_display()})"

    @property
    def is_overdue(self) -> bool:
        """
        Retorna se a transação está logicamente vencida.
        Ocorre se o status for pendente, houver data de vencimento e ela for menor que hoje.
        """
        if self.payment_status == self.PaymentStatus.PENDING and self.due_date:
            return self.due_date < timezone.localdate()
        return False

    def can_pay(self) -> bool:
        """Só permite pagar se estiver pendente."""
        return self.payment_status == self.PaymentStatus.PENDING

    def can_cancel(self) -> bool:
        """Só permite cancelar se estiver pendente."""
        return self.payment_status == self.PaymentStatus.PENDING

    def can_refund(self) -> bool:
        """Só permite estornar se estiver paga."""
        return self.payment_status == self.PaymentStatus.PAID

    def pay(self, payment_method: str = "pix", paid_at=None) -> None:
        """Registra o pagamento da transação."""
        from django.core.exceptions import ValidationError
        if not self.can_pay():
            raise ValidationError(_("Esta transação não está pendente de pagamento."))
        self.payment_status = self.PaymentStatus.PAID
        self.payment_method = payment_method
        self.paid_at = paid_at or timezone.now()
        self.save()

        # Atualiza a consulta associada (se houver) para status confirmado
        if self.appointment:
            appointment = self.appointment
            if appointment.status == appointment.Status.SCHEDULED:
                appointment.status = appointment.Status.CONFIRMED
                appointment.save(update_fields=["status", "updated_at"])

    def cancel(self) -> None:
        """Cancela a transação pendente."""
        from django.core.exceptions import ValidationError
        if not self.can_cancel():
            raise ValidationError(_("Apenas transações pendentes podem ser canceladas."))
        self.payment_status = self.PaymentStatus.CANCELLED
        self.save()

    def refund(self) -> None:
        """Estorna a transação paga."""
        from django.core.exceptions import ValidationError
        if not self.can_refund():
            raise ValidationError(_("Apenas transações pagas podem ser estornadas."))
        self.payment_status = self.PaymentStatus.REFUNDED
        self.save()

    # ── Classmethod: resumo mensal ───────────────────────────────────────────
    @classmethod
    def monthly_summary(cls, therapist, year: int, month: int) -> dict:
        """
        Retorna um dicionário com o resumo financeiro de um terapeuta
        em um determinado mês/ano.

        Args:
            therapist: Instância ou PK do usuário terapeuta.
            year (int): Ano de referência.
            month (int): Mês de referência (1–12).

        Returns:
            dict com as chaves:
                - total_income   (Decimal): soma das receitas pagas no mês
                - total_expense  (Decimal): soma das despesas pagas no mês
                - balance        (Decimal): total_income - total_expense
                - total_pending  (Decimal): soma de transações pendentes no mês
                - transaction_count (int): total de transações no mês
        """
        from decimal import Decimal

        # Filtra transações do mês/ano independentemente do status
        qs_month = cls.objects.filter(
            therapist=therapist,
            created_at__year=year,
            created_at__month=month,
        )

        # Transações pagas no mês (base para income/expense)
        qs_paid = qs_month.filter(payment_status=cls.PaymentStatus.PAID)

        total_income = (
            qs_paid.filter(transaction_type=cls.TransactionType.INCOME)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        total_expense = (
            qs_paid.filter(transaction_type=cls.TransactionType.EXPENSE)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        total_pending = (
            qs_month.filter(payment_status=cls.PaymentStatus.PENDING)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        return {
            "year": year,
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "total_pending": total_pending,
            "transaction_count": qs_month.count(),
        }
