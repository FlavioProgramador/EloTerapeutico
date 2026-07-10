from django.conf import settings
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
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    currency = models.CharField(max_length=3, default="BRL", verbose_name="Moeda")
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name="Ciclo de cobrança",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    max_patients = models.PositiveIntegerField(null=True, blank=True, verbose_name="Limite de pacientes")
    max_storage_mb = models.PositiveIntegerField(null=True, blank=True, verbose_name="Limite de armazenamento (MB)")
    has_agenda = models.BooleanField(default=True, verbose_name="Agenda")
    has_patients = models.BooleanField(default=True, verbose_name="Pacientes")
    has_clinical_records = models.BooleanField(default=True, verbose_name="Prontuários")
    has_financial = models.BooleanField(default=False, verbose_name="Financeiro")
    has_documents = models.BooleanField(default=False, verbose_name="Documentos")
    has_forms = models.BooleanField(default=False, verbose_name="Formulários")
    has_reports = models.BooleanField(default=False, verbose_name="Relatórios")
    has_ai = models.BooleanField(default=False, verbose_name="IA")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ["price", "name"]
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


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = "TRIALING", "Em teste"
        PENDING = "PENDING", "Pendente"
        ACTIVE = "ACTIVE", "Ativa"
        PAST_DUE = "PAST_DUE", "Em atraso"
        CANCELED = "CANCELED", "Cancelada"
        EXPIRED = "EXPIRED", "Expirada"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Usuário",
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions", verbose_name="Plano")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciada em")
    trial_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Fim do trial")
    current_period_start = models.DateTimeField(null=True, blank=True, verbose_name="Início do período atual")
    current_period_end = models.DateTimeField(null=True, blank=True, verbose_name="Fim do período atual")
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelada em")
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_customer_id = models.CharField(max_length=120, blank=True)
    gateway_subscription_id = models.CharField(max_length=120, blank=True, db_index=True)
    gateway_status = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criada em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizada em")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        indexes = [
            models.Index(fields=["user", "status"], name="billing_sub_user_status_idx"),
            models.Index(fields=["gateway_subscription_id"], name="billing_sub_gateway_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def is_trial_valid(self) -> bool:
        return bool(self.status == self.Status.TRIALING and self.trial_ends_at and self.trial_ends_at >= timezone.now())


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        CONFIRMED = "CONFIRMED", "Confirmado"
        RECEIVED = "RECEIVED", "Recebido"
        OVERDUE = "OVERDUE", "Vencido"
        REFUNDED = "REFUNDED", "Estornado"
        CANCELED = "CANCELED", "Cancelado"
        FAILED = "FAILED", "Falhou"

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_payment_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    gateway_subscription_id = models.CharField(max_length=120, blank=True, db_index=True)
    invoice_url = models.URLField(blank=True)
    bank_slip_url = models.URLField(blank=True)
    pix_qr_code = models.TextField(blank=True)
    pix_copy_paste = models.TextField(blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-due_date", "-created_at"]
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        indexes = [
            models.Index(fields=["user", "status"], name="billing_pay_user_status_idx"),
            models.Index(fields=["gateway_subscription_id"], name="billing_pay_sub_gateway_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="billing_payment_amount_positive",
            ),
        ]

    def __str__(self) -> str:
        return f"Pagamento {self.gateway_payment_id or self.pk} — {self.status}"


class WebhookEvent(models.Model):
    gateway_name = models.CharField(max_length=40)
    event_id = models.CharField(max_length=160, unique=True, null=True, blank=True)
    event_type = models.CharField(max_length=120)
    payload_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Evento de webhook"
        verbose_name_plural = "Eventos de webhook"
        indexes = [models.Index(fields=["gateway_name", "event_type"], name="billing_webhook_type_idx")]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(processed=False, processed_at__isnull=True)
                    | Q(processed=True, processed_at__isnull=False)
                ),
                name="billing_webhook_processed_timestamp_consistent",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.gateway_name} — {self.event_type}"


class FeatureUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feature_usages")
    feature_key = models.CharField(max_length=80)
    usage_count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "feature_key", "period_start", "period_end")
        ordering = ["-period_start"]
        verbose_name = "Uso de recurso"
        verbose_name_plural = "Uso de recursos"

    def __str__(self) -> str:
        return f"{self.user} — {self.feature_key}: {self.usage_count}"
