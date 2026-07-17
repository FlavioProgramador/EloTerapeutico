from django.contrib import admin

from apps.billing.models import FeatureUsage


@admin.register(FeatureUsage)
class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "feature_key",
        "usage_count",
        "period_start",
        "period_end",
    )
    list_filter = ("feature_key", "period_start", "period_end")
    search_fields = ("user__email", "user__full_name", "feature_key")
    readonly_fields = ("created_at", "updated_at")
