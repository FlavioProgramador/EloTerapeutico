from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .catalog import Plan
from .orders import BillingOrder


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = "TRIALING", "Em teste"
        PENDING = "PENDING", "Pendente"
        ACTIVE = "ACTIVE", "Ativa"
        PAST_DUE = "PAST_DUE", "Em atraso"
        SUSPENDED = "SUSPENDED", "Suspensa"
        CANCELED = "CANCELED", "Cancelada"
        EXPIRED = "EXPIRED", "Expirada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Usuário",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        verbose_name="Plano",
    )
    billing_order = models.ForeignKey(
        BillingOrder,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Iniciada em",
    )
    access_starts_at = models.DateTimeField(null=True, blank=True)
    access_ends_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fim do trial",
    )
    current_period_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Início do período atual",
    )
    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fim do período atual",
    )
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Cancelada em",
    )
    suspended_at = models.DateTimeField(null=True, blank=True)
    reactivated_at = models.DateTimeField(null=True, blank=True)
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_customer_id = models.CharField(max_length=120, blank=True)
    gateway_subscription_id = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    gateway_status = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        indexes = [
            models.Index(
                fields=["user", "status"],
                name="billing_sub_user_status_idx",
            ),
            models.Index(
                fields=["gateway_subscription_id"],
                name="billing_sub_gateway_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(
                    status__in=[
                        "TRIALING",
                        "PENDING",
                        "ACTIVE",
                        "PAST_DUE",
                        "SUSPENDED",
                    ]
                ),
                name="billing_one_operational_subscription",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def is_trial_valid(self) -> bool:
        return bool(
            self.status == self.Status.TRIALING
            and self.trial_ends_at
            and self.trial_ends_at >= timezone.now()
        )

    @property
    def has_access(self) -> bool:
        now = timezone.now()
        return bool(
            self.status
            in {
                self.Status.TRIALING,
                self.Status.ACTIVE,
                self.Status.PAST_DUE,
            }
            and (self.access_starts_at is None or self.access_starts_at <= now)
            and (self.access_ends_at is None or self.access_ends_at >= now)
            and (
                self.status != self.Status.PAST_DUE
                or self.grace_period_ends_at is None
                or self.grace_period_ends_at >= now
            )
        )
