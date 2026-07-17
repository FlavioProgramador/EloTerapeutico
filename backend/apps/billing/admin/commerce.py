from django.contrib import admin

from apps.billing.models import BillingOrder, Payment, Subscription


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
    list_filter = (
        "status",
        "billing_model",
        "billing_interval",
        "gateway_name",
        "created_at",
    )
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
    list_filter = (
        "status",
        "plan",
        "gateway_name",
        "cancel_at_period_end",
        "created_at",
    )
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
    list_filter = (
        "status",
        "billing_type",
        "currency",
        "gateway_name",
        "due_date",
        "created_at",
    )
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
