from django.contrib import admin

from apps.billing.models import Plan, PlanPrice


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
    list_filter = (
        "billing_interval",
        "billing_model",
        "is_active",
        "currency",
    )
    search_fields = ("name", "slug", "plan__name")
    readonly_fields = ("created_at", "updated_at")
