from django.contrib import admin

from .models import FeatureUsage, Payment, Plan, Subscription, WebhookEvent


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "currency", "billing_cycle", "is_active", "max_patients")
    list_filter = ("is_active", "billing_cycle", "has_financial", "has_reports", "has_ai")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "gateway_name", "gateway_subscription_id", "current_period_end")
    list_filter = ("status", "plan", "gateway_name", "created_at")
    search_fields = ("user__email", "user__full_name", "plan__name", "gateway_customer_id", "gateway_subscription_id")
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
    list_display = ("user", "subscription", "amount", "currency", "status", "due_date", "paid_at", "gateway_payment_id")
    list_filter = ("status", "currency", "gateway_name", "due_date", "created_at")
    search_fields = ("user__email", "user__full_name", "gateway_payment_id", "gateway_subscription_id")
    readonly_fields = (
        "gateway_payment_id",
        "gateway_subscription_id",
        "invoice_url",
        "bank_slip_url",
        "pix_qr_code",
        "pix_copy_paste",
        "raw_payload",
        "created_at",
        "updated_at",
    )

    def has_change_permission(self, request, obj=None):
        if obj and "status" in request.POST:
            return request.user.is_superuser
        return super().has_change_permission(request, obj)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("gateway_name", "event_type", "event_id", "processed", "received_at", "processed_at")
    list_filter = ("gateway_name", "event_type", "processed", "received_at")
    search_fields = ("event_id", "payload_hash", "error_message")
    readonly_fields = ("gateway_name", "event_id", "event_type", "payload_hash", "payload", "processed_at", "received_at")


@admin.register(FeatureUsage)
class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "feature_key", "usage_count", "period_start", "period_end")
    list_filter = ("feature_key", "period_start", "period_end")
    search_fields = ("user__email", "user__full_name", "feature_key")
    readonly_fields = ("created_at", "updated_at")
