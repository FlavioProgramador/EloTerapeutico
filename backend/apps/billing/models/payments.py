from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from .orders import BillingOrder
from .subscriptions import Subscription


class Payment(models.Model):
    class BillingType(models.TextChoices):
        PIX = "PIX", "Pix"
        BOLETO = "BOLETO", "Boleto"
        CREDIT_CARD = "CREDIT_CARD", "Cartão de crédito"
        UNDEFINED = "UNDEFINED", "Não definido"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        AUTHORIZED = "AUTHORIZED", "Autorizado"
        CONFIRMED = "CONFIRMED", "Confirmado"
        RECEIVED = "RECEIVED", "Recebido"
        OVERDUE = "OVERDUE", "Vencido"
        FAILED = "FAILED", "Falhou"
        CANCELED = "CANCELED", "Cancelado"
        REFUNDED = "REFUNDED", "Estornado"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Parcialmente estornado"
        REFUND_IN_PROGRESS = "REFUND_IN_PROGRESS", "Estorno em andamento"
        CHARGEBACK = "CHARGEBACK", "Chargeback"
        CHARGEBACK_DISPUTE = "CHARGEBACK_DISPUTE", "Disputa de chargeback"
        RESTORED = "RESTORED", "Restaurado"
        AWAITING_RISK_ANALYSIS = "AWAITING_RISK_ANALYSIS", "Em análise de risco"

    billing_order = models.ForeignKey(
        BillingOrder,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name="payments",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    interest_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    currency = models.CharField(max_length=3, default="BRL")
    billing_type = models.CharField(
        max_length=20,
        choices=BillingType.choices,
        default=BillingType.UNDEFINED,
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    due_date = models.DateField(null=True, blank=True)
    original_due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    credit_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_payment_id = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
    )
    gateway_subscription_id = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    gateway_installment_id = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    installment_number = models.PositiveSmallIntegerField(null=True, blank=True)
    installment_count = models.PositiveSmallIntegerField(default=1)
    invoice_number = models.CharField(max_length=120, blank=True)
    invoice_url = models.URLField(blank=True)
    bank_slip_url = models.URLField(blank=True)
    transaction_receipt_url = models.URLField(blank=True)
    pix_qr_code = models.TextField(blank=True)
    pix_copy_paste = models.TextField(blank=True)
    external_reference = models.CharField(max_length=160, blank=True, db_index=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "installment_number", "created_at"]
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="billing_pay_user_status_idx",
            ),
            models.Index(
                fields=["gateway_subscription_id"],
                name="billing_pay_sub_gateway_idx",
            ),
            models.Index(
                fields=["gateway_installment_id"],
                name="billing_pay_installment_idx",
            ),
            models.Index(
                fields=["billing_order", "installment_number"],
                name="billing_pay_order_number_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="billing_payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(installment_count__gte=1),
                name="billing_payment_installment_positive",
            ),
            models.UniqueConstraint(
                fields=["billing_order", "installment_number"],
                condition=Q(
                    billing_order__isnull=False,
                    installment_number__isnull=False,
                ),
                name="billing_unique_order_installment",
            ),
        ]

    def __str__(self) -> str:
        return f"Pagamento {self.gateway_payment_id or self.pk} — {self.status}"
