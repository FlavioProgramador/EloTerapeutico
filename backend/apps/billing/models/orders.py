from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from .catalog import Plan, PlanPrice


class BillingOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        PENDING = "PENDING", "Pendente"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Parcialmente pago"
        PAID = "PAID", "Pago"
        OVERDUE = "OVERDUE", "Em atraso"
        CANCELED = "CANCELED", "Cancelado"
        REFUNDED = "REFUNDED", "Estornado"
        PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Parcialmente estornado"
        CHARGEBACK = "CHARGEBACK", "Chargeback"
        FAILED = "FAILED", "Falhou"
        EXPIRED = "EXPIRED", "Expirado"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_orders",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="billing_orders",
    )
    plan_price = models.ForeignKey(
        PlanPrice,
        on_delete=models.PROTECT,
        related_name="billing_orders",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    billing_model = models.CharField(
        max_length=20,
        choices=PlanPrice.BillingModel.choices,
    )
    billing_interval = models.CharField(
        max_length=20,
        choices=PlanPrice.BillingInterval.choices,
    )
    currency = models.CharField(max_length=3, default="BRL")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    installment_count = models.PositiveSmallIntegerField(default=1)
    installment_amount_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_customer_id = models.CharField(max_length=120, blank=True)
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
    external_reference = models.CharField(max_length=160, unique=True)
    idempotency_key = models.CharField(max_length=160, unique=True)
    commercial_snapshot = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Contratação"
        verbose_name_plural = "Contratações"
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gt=0),
                name="billing_order_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(installment_count__gte=1),
                name="billing_order_installment_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="billing_order_user_status_idx",
            ),
            models.Index(
                fields=["gateway_installment_id"],
                name="billing_order_installment_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.public_id} — {self.plan} ({self.status})"
