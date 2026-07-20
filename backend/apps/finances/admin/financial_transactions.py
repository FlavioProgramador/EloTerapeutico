"""Admin de transações financeiras."""

from decimal import Decimal

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RangeDateFilter,
)

from apps.finances.models import FinancialTransaction
from apps.finances.selectors import admin_changelist_summary
from apps.finances.services import cancel_transaction, register_payment


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(ModelAdmin):
    list_display = (
        "id", "therapist_name", "patient_name", "transaction_type_badge",
        "category_display", "amount_display", "paid_amount_display",
        "outstanding_amount_display", "payment_method_display",
        "payment_status_badge", "due_date", "paid_at", "created_at",
    )
    list_display_links = ("id", "therapist_name")
    list_filter = (
        ("transaction_type", ChoicesDropdownFilter),
        ("payment_status", ChoicesDropdownFilter),
        ("payment_method", ChoicesDropdownFilter),
        ("category", ChoicesDropdownFilter),
        ("source", ChoicesDropdownFilter),
        ("is_recurring", BooleanRadioFilter),
        ("due_date", RangeDateFilter),
        ("created_at", RangeDateFilter),
    )
    search_fields = (
        "therapist__full_name", "therapist__email", "patient__full_name",
        "description", "beneficiary",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("therapist", "patient", "appointment")
    autocomplete_fields = ("therapist", "patient")
    raw_id_fields = ("appointment", "subscription")
    readonly_fields = ("created_at", "updated_at", "outstanding_amount_display")
    actions = ("action_cancel_pending", "action_mark_paid")
    fieldsets = (
        (_("Relacionamentos"), {"fields": ("therapist", "patient", "appointment", "subscription")}),
        (_("Dados da transação"), {"fields": (
            "transaction_type", "category", "source", "amount", "paid_amount",
            "outstanding_amount_display", "payment_method", "payment_status",
            "description", "beneficiary",
        )}),
        (_("Datas"), {"fields": ("due_date", "paid_at")}),
        (_("Recorrência"), {"fields": ("is_recurring", "recurrence_frequency", "recurrence_end_date"), "classes": ("collapse",)}),
        (_("Documentação"), {"fields": ("payment_link", "receipt_url"), "classes": ("collapse",)}),
        (_("Auditoria"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.action(description=_("Cancelar transações pendentes selecionadas"))
    def action_cancel_pending(self, request, queryset):
        if not request.user.has_perm("financeiro.change_financialtransaction"):
            self.message_user(request, _("Permissão insuficiente."), messages.ERROR)
            return
        count = 0
        for item in queryset:
            if item.can_cancel():
                cancel_transaction(financial_transaction=item)
                count += 1
        self.message_user(request, _("%(count)s transação(ões) cancelada(s).") % {"count": count}, messages.WARNING)

    @admin.action(description=_("Marcar transações selecionadas como Pagas"))
    def action_mark_paid(self, request, queryset):
        if not request.user.has_perm("financeiro.change_financialtransaction"):
            self.message_user(request, _("Permissão insuficiente."), messages.ERROR)
            return
        count = 0
        for item in queryset:
            if item.can_pay():
                register_payment(
                    financial_transaction=item,
                    payment_method=item.payment_method or FinancialTransaction.PaymentMethod.PIX,
                )
                count += 1
        self.message_user(request, _("%(count)s transação(ões) marcada(s) como paga(s).") % {"count": count}, messages.SUCCESS)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("therapist", "patient", "appointment")
        return queryset if request.user.is_superuser else queryset.filter(therapist=request.user)

    @admin.display(description=_("Terapeuta"), ordering="therapist__full_name")
    def therapist_name(self, obj):
        return obj.therapist.full_name

    @admin.display(description=_("Paciente"), ordering="patient__full_name")
    def patient_name(self, obj):
        return obj.patient.full_name if obj.patient else "–"

    @admin.display(description=_("Tipo"), ordering="transaction_type")
    def transaction_type_badge(self, obj):
        color = "#15803d" if obj.transaction_type == "income" else "#b91c1c"
        return format_html('<span style="background:{};color:#fff;padding:2px 8px;border-radius:999px;font-size:11px;">{}</span>', color, obj.get_transaction_type_display())

    @admin.display(description=_("Categoria"), ordering="category")
    def category_display(self, obj):
        return obj.get_category_display()

    @admin.display(description=_("Valor"), ordering="amount")
    def amount_display(self, obj):
        color = "#15803d" if obj.transaction_type == "income" else "#b91c1c"
        return format_html('<strong style="color:{};">{}</strong>', color, self._format_brl(obj.amount))

    @admin.display(description=_("Pago"), ordering="paid_amount")
    def paid_amount_display(self, obj):
        return self._format_brl(obj.paid_amount)

    @admin.display(description=_("Em aberto"))
    def outstanding_amount_display(self, obj):
        return self._format_brl(obj.outstanding_amount)

    @admin.display(description=_("Método"), ordering="payment_method")
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()

    @admin.display(description=_("Status"), ordering="payment_status")
    def payment_status_badge(self, obj):
        colors = {
            "paid": ("#15803d", "#fff"), "partial": ("#0369a1", "#fff"),
            "pending": ("#ca8a04", "#111827"), "cancelled": ("#6b7280", "#fff"),
            "refunded": ("#7c3aed", "#fff"),
        }
        color, text_color = colors.get(obj.payment_status, ("#6b7280", "#fff"))
        return format_html('<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:11px;">{}</span>', color, text_color, obj.get_payment_status_display())

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            queryset = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response
        response.context_data["summary"] = admin_changelist_summary(queryset)
        return response

    @staticmethod
    def _format_brl(value: Decimal | None) -> str:
        amount = value or Decimal("0.00")
        formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
