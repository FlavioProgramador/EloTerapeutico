from django.contrib import admin

from .models import BillingOrder, FeatureUsage, Payment, Plan, PlanPrice, Subscription, WebhookEvent


class PlanPriceInline(admin.TabularInline):
    model = PlanPrice
    extra = 0
    fields = (
        "name",
        "slug",
        "billing_interval",
        "billing_model",
        "total_amount",
        "installments_enabled",
        "max_installments",
        "is_active",
    )


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "max_patients")
    list_filter = ("is_active", "has_financial", "has_reports", "has_ai")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = [PlanPriceInline]


@admin.register(PlanPrice)
class PlanPriceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "plan",
        "billing_interval",
        "billing_model",
        "total_amount",
        "max_installments",
        "is_active",
    )
    list_filter = ("billing_interval", "billing_model", "is_active", "currency")
    search_fields = ("name", "slug", "plan__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BillingOrder)
class BillingOrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "user",
        "plan",
        "status",
        "billing_model",
        "total_amount",
        "installment_count",
        "created_at",
    )
    list_filter = ("status", "billing_model", "billing_interval", "gateway_name", "created_at")
    search_fields = (
        "public_id",
        "user__email",
        "user__full_name",
        "external_reference",
        "gateway_subscription_id",
        "gateway_installment_id",
    )
    readonly_fields = (
        "public_id",
        "external_reference",
        "idempotency_key",
        "commercial_snapshot",
        "metadata",
        "created_at",
        "updated_at",
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status",
        "cancel_at_period_end",
        "access_ends_at",
        "gateway_subscription_id",
    )
    list_filter = ("status", "plan", "gateway_name", "cancel_at_period_end", "created_at")
    search_fields = (
        "user__email",
        "user__full_name",
        "plan__name",
        "gateway_customer_id",
        "gateway_subscription_id",
        "billing_order__public_id",
    )
    readonly_fields = (
        "gateway_customer_id",
        "gateway_subscription_id",
        "gateway_status",
        "metadata",
        "created_at",
        "updated_at",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "billing_order",
        "installment_label",
        "amount",
        "status",
        "billing_type",
        "due_date",
        "paid_at",
    )
    list_filter = ("status", "billing_type", "currency", "gateway_name", "due_date", "created_at")
    search_fields = (
        "user__email",
        "user__full_name",
        "gateway_payment_id",
        "gateway_subscription_id",
        "gateway_installment_id",
        "external_reference",
    )
    readonly_fields = (
        "gateway_payment_id",
        "gateway_subscription_id",
        "gateway_installment_id",
        "invoice_url",
        "bank_slip_url",
        "transaction_receipt_url",
        "pix_qr_code",
        "pix_copy_paste",
        "raw_payload",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Parcela")
    def installment_label(self, obj):
        if obj.installment_number:
            return f"{obj.installment_number}/{obj.installment_count}"
        return "À vista"

    def has_change_permission(self, request, obj=None):
        if obj and "status" in request.POST:
            return request.user.is_superuser
        return super().has_change_permission(request, obj)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "gateway_name",
        "event_type",
        "event_id",
        "status",
        "attempt_count",
        "received_at",
        "processed_at",
    )
    list_filter = ("gateway_name", "event_type", "status", "received_at")
    search_fields = ("event_id", "payload_hash", "last_error", "error_message")
    readonly_fields = (
        "gateway_name",
        "event_id",
        "event_type",
        "payload_hash",
        "payload",
        "attempt_count",
        "processed_at",
        "received_at",
        "updated_at",
    )


@admin.register(FeatureUsage)
class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "feature_key", "usage_count", "period_start", "period_end")
    list_filter = ("feature_key", "period_start", "period_end")
    search_fields = ("user__email", "user__full_name", "feature_key")
    readonly_fields = ("created_at", "updated_at")
