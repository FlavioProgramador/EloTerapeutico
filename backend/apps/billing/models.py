import uuid

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
    # Campos legados mantidos durante a migração. Novas contratações usam PlanPrice.
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço legado")
    currency = models.CharField(max_length=3, default="BRL", verbose_name="Moeda legada")
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        verbose_name="Ciclo legado",
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
        ordering = ["name"]
        verbose_name = "Plano"
        verbose_name_plural = "Planos"
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="billing_plan_price_non_negative"),
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
    billing_interval = models.CharField(max_length=20, choices=BillingInterval.choices)
    billing_model = models.CharField(max_length=20, choices=BillingModel.choices)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
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
            models.CheckConstraint(condition=Q(total_amount__gt=0), name="billing_price_amount_positive"),
            models.CheckConstraint(
                condition=Q(discount_percentage__gte=0, discount_percentage__lte=100),
                name="billing_price_discount_range",
            ),
            models.CheckConstraint(
                condition=Q(min_installments__gte=1) & Q(max_installments__gte=models.F("min_installments")),
                name="billing_price_installment_range",
            ),
        ]
        indexes = [
            models.Index(fields=["plan", "is_active"], name="billing_price_plan_active_idx"),
            models.Index(fields=["billing_interval", "billing_model"], name="billing_price_mode_idx"),
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_orders")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="billing_orders")
    plan_price = models.ForeignKey(PlanPrice, on_delete=models.PROTECT, related_name="billing_orders")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT, db_index=True)
    billing_model = models.CharField(max_length=20, choices=PlanPrice.BillingModel.choices)
    billing_interval = models.CharField(max_length=20, choices=PlanPrice.BillingInterval.choices)
    currency = models.CharField(max_length=3, default="BRL")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment_count = models.PositiveSmallIntegerField(default=1)
    installment_amount_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_customer_id = models.CharField(max_length=120, blank=True)
    gateway_subscription_id = models.CharField(max_length=120, blank=True, db_index=True)
    gateway_installment_id = models.CharField(max_length=120, blank=True, db_index=True)
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
            models.CheckConstraint(condition=Q(total_amount__gt=0), name="billing_order_amount_positive"),
            models.CheckConstraint(condition=Q(installment_count__gte=1), name="billing_order_installment_positive"),
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="billing_order_user_status_idx"),
            models.Index(fields=["gateway_installment_id"], name="billing_order_installment_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.public_id} — {self.plan} ({self.status})"


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
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions", verbose_name="Plano")
    billing_order = models.ForeignKey(
        BillingOrder,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciada em")
    access_starts_at = models.DateTimeField(null=True, blank=True)
    access_ends_at = models.DateTimeField(null=True, blank=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True, verbose_name="Fim do trial")
    current_period_start = models.DateTimeField(null=True, blank=True, verbose_name="Início do período atual")
    current_period_end = models.DateTimeField(null=True, blank=True, verbose_name="Fim do período atual")
    grace_period_ends_at = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="Cancelada em")
    suspended_at = models.DateTimeField(null=True, blank=True)
    reactivated_at = models.DateTimeField(null=True, blank=True)
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
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status__in=["TRIALING", "PENDING", "ACTIVE", "PAST_DUE", "SUSPENDED"]),
                name="billing_one_operational_subscription",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def is_trial_valid(self) -> bool:
        return bool(self.status == self.Status.TRIALING and self.trial_ends_at and self.trial_ends_at >= timezone.now())

    @property
    def has_access(self) -> bool:
        now = timezone.now()
        return bool(
            self.status in {self.Status.TRIALING, self.Status.ACTIVE, self.Status.PAST_DUE}
            and (self.access_starts_at is None or self.access_starts_at <= now)
            and (self.access_ends_at is None or self.access_ends_at >= now)
            and (self.status != self.Status.PAST_DUE or self.grace_period_ends_at is None or self.grace_period_ends_at >= now)
        )


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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="billing_payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")
    billing_type = models.CharField(max_length=20, choices=BillingType.choices, default=BillingType.UNDEFINED)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    original_due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    credit_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    gateway_name = models.CharField(max_length=40, default="ASAAS")
    gateway_payment_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    gateway_subscription_id = models.CharField(max_length=120, blank=True, db_index=True)
    gateway_installment_id = models.CharField(max_length=120, blank=True, db_index=True)
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
            models.Index(fields=["user", "status"], name="billing_pay_user_status_idx"),
            models.Index(fields=["gateway_subscription_id"], name="billing_pay_sub_gateway_idx"),
            models.Index(fields=["gateway_installment_id"], name="billing_pay_installment_idx"),
            models.Index(fields=["billing_order", "installment_number"], name="billing_pay_order_number_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="billing_payment_amount_positive"),
            models.CheckConstraint(condition=Q(installment_count__gte=1), name="billing_payment_installment_positive"),
            models.UniqueConstraint(
                fields=["billing_order", "installment_number"],
                condition=Q(billing_order__isnull=False, installment_number__isnull=False),
                name="billing_unique_order_installment",
            ),
        ]

    def __str__(self) -> str:
        return f"Pagamento {self.gateway_payment_id or self.pk} — {self.status}"


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recebido"
        PROCESSING = "PROCESSING", "Processando"
        PROCESSED = "PROCESSED", "Processado"
        RETRY = "RETRY", "Aguardando nova tentativa"
        FAILED = "FAILED", "Falhou"
        IGNORED = "IGNORED", "Ignorado"

    gateway_name = models.CharField(max_length=40)
    event_id = models.CharField(max_length=160, unique=True, null=True, blank=True)
    event_type = models.CharField(max_length=120)
    payload_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED, db_index=True)
    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    # Compatibilidade temporária com o contrato anterior.
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Evento de webhook"
        verbose_name_plural = "Eventos de webhook"
        indexes = [
            models.Index(fields=["gateway_name", "event_type"], name="billing_webhook_type_idx"),
            models.Index(fields=["status", "next_retry_at"], name="billing_webhook_retry_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(Q(processed=False, processed_at__isnull=True) | Q(processed=True, processed_at__isnull=False)),
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
