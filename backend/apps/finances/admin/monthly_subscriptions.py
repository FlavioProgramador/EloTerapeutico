"""Admin de mensalidades recorrentes de pacientes."""

from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter

from apps.finances.models import MonthlySubscription
from apps.finances.services import change_monthly_subscription_status


@admin.register(MonthlySubscription)
class MonthlySubscriptionAdmin(ModelAdmin):
    list_display = (
        "id", "patient", "therapist", "status", "frequency",
        "monthly_amount", "due_day", "next_billing_date", "updated_at",
    )
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("frequency", ChoicesDropdownFilter),
        ("next_billing_date", RangeDateFilter),
    )
    search_fields = ("patient__full_name", "therapist__full_name", "therapist__email")
    autocomplete_fields = ("patient", "therapist")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("patient", "therapist")
    actions = ("pause_selected", "activate_selected")

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("patient", "therapist")
        return queryset if request.user.is_superuser else queryset.filter(therapist=request.user)

    @admin.action(description="Pausar mensalidades selecionadas")
    def pause_selected(self, request, queryset):
        for item in queryset:
            change_monthly_subscription_status(
                actor=item.therapist, monthly_subscription=item, target_status=MonthlySubscription.Status.PAUSED
            )

    @admin.action(description="Ativar mensalidades selecionadas")
    def activate_selected(self, request, queryset):
        for item in queryset:
            change_monthly_subscription_status(
                actor=item.therapist, monthly_subscription=item, target_status=MonthlySubscription.Status.ACTIVE
            )
