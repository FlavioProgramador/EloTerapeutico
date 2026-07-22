from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone


class Plan(models.Model):
    class BillingCycle(models.TextChoices):
        MONTHLY = "MONTHLY", "Mensal"
        YEARLY = "YEARLY", "Anual"

    name = models.CharField(max_length=120, verbose_name="Nome")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Descrição")
    # Campos legados mantidos durante a migração. Novas contratações usam PlanPrice.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Preço legado",
    )
    currency = models.CharField(
        max_length=3,
        default="BRL",
        verbose_name="Moeda legada",
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name="Ciclo legado",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    max_patients = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Limite de pacientes",
    )
    max_storage_mb = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Limite de armazenamento (MB)",
    )
    has_agenda = models.BooleanField(default=True, verbose_name="Agenda")
    has_patients = models.BooleanField(default=True, verbose_name="Pacientes")
    has_clinical_records = models.BooleanField(
        default=True,
        verbose_name="Prontuários",
    )
    has_financial = models.BooleanField(default=False, verbose_name="Financeiro")
    has_documents = models.BooleanField(default=False, verbose_name="Documentos")
    has_forms = models.BooleanField(default=False, verbose_name="Formulários")
    has_reports = models.BooleanField(default=False, verbose_name="Relatórios")
    has_telemedicine = models.BooleanField(
        default=False,
        verbose_name="Telemedicina",
    )
    has_ai = models.BooleanField(default=False, verbose_name="IA")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ["name"]
        verbose_name = "Plano"
        verbose_name_plural = "Planos"
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="billing_plan_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class PlanPrice(models.Model):
    class BillingInterval(models.TextChoices):
        MONTHLY = "MONTHLY", "Mensal"
        YEARLY = "YEARLY", "Anual"

    class BillingModel(models.TextChoices):
        RECURRING = "RECURRING", "Recorrente"
        ONE_TIME = "ONE_TIME", "À vista"
        INSTALLMENT = "INSTALLMENT", "Parcelado"

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="prices")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    currency = models.CharField(max_length=3, default="BRL")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
    )
    billing_model = models.CharField(max_length=20, choices=BillingModel.choices)
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    installments_enabled = models.BooleanField(default=False)
    min_installments = models.PositiveSmallIntegerField(default=1)
    max_installments = models.PositiveSmallIntegerField(default=1)
    trial_days = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["plan__name", "billing_interval", "total_amount"]
        verbose_name = "Preço do plano"
        verbose_name_plural = "Preços dos planos"
        constraints = [
            models.CheckConstraint(
                condition=Q(total_amount__gt=0),
                name="billing_price_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    discount_percentage__gte=0,
                    discount_percentage__lte=100,
                ),
                name="billing_price_discount_range",
            ),
            models.CheckConstraint(
                condition=Q(min_installments__gte=1)
                & Q(max_installments__gte=models.F("min_installments")),
                name="billing_price_installment_range",
            ),
        ]
        indexes = [
            models.Index(
                fields=["plan", "is_active"],
                name="billing_price_plan_active_idx",
            ),
            models.Index(
                fields=["billing_interval", "billing_model"],
                name="billing_price_mode_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.plan} — {self.name}"

    def is_available(self, at=None) -> bool:
        at = at or timezone.now()
        return bool(
            self.is_active
            and self.plan.is_active
            and (self.starts_at is None or self.starts_at <= at)
            and (self.ends_at is None or self.ends_at >= at)
        )
