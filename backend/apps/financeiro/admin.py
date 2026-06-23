"""
apps/financeiro/admin.py
Admin do módulo financeiro com listagem rica e agregações.
"""

from decimal import Decimal

from django.contrib import admin
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import FinancialTransaction


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    """
    Interface administrativa para FinancialTransaction.
    Exibe somatórios de receita/despesa no rodapé da listagem.
    """

    # ── Exibição na listagem ─────────────────────────────────────────────────
    list_display = (
        "id",
        "therapist_name",
        "patient_name",
        "transaction_type_badge",
        "category_display",
        "amount_display",
        "payment_method_display",
        "payment_status_badge",
        "due_date",
        "paid_at",
        "created_at",
    )
    list_display_links = ("id", "therapist_name")
    list_filter = (
        "transaction_type",
        "payment_status",
        "payment_method",
        "category",
        "created_at",
    )
    search_fields = (
        "therapist__full_name",
        "therapist__email",
        "patient__full_name",
        "description",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    # ── Formulário de edição ─────────────────────────────────────────────────
    fieldsets = (
        (
            _("Relacionamentos"),
            {
                "fields": ("therapist", "patient", "appointment"),
            },
        ),
        (
            _("Dados da Transação"),
            {
                "fields": (
                    "transaction_type",
                    "category",
                    "amount",
                    "payment_method",
                    "payment_status",
                    "description",
                ),
            },
        ),
        (
            _("Datas"),
            {
                "fields": ("due_date", "paid_at"),
            },
        ),
        (
            _("Documentação"),
            {
                "fields": ("receipt_url",),
                "classes": ("collapse",),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("patient",)
    raw_id_fields = ("appointment",)

    # ── Campos personalizados na listagem ────────────────────────────────────
    @admin.display(description=_("Terapeuta"), ordering="therapist__full_name")
    def therapist_name(self, obj):
        return obj.therapist.full_name

    @admin.display(description=_("Paciente"), ordering="patient__full_name")
    def patient_name(self, obj):
        if obj.patient:
            return obj.patient.full_name
        return "–"

    @admin.display(description=_("Tipo"), ordering="transaction_type")
    def transaction_type_badge(self, obj):
        """Exibe o tipo como badge colorido."""
        color = "#28a745" if obj.transaction_type == "income" else "#dc3545"
        label = obj.get_transaction_type_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">'
            "{}</span>",
            color,
            label,
        )

    @admin.display(description=_("Categoria"), ordering="category")
    def category_display(self, obj):
        return obj.get_category_display()

    @admin.display(description=_("Valor"), ordering="amount")
    def amount_display(self, obj):
        """Exibe o valor formatado em BRL."""
        color = "#28a745" if obj.transaction_type == "income" else "#dc3545"
        return format_html(
            '<strong style="color:{};">R$ {:,.2f}</strong>',
            color,
            obj.amount,
        )

    @admin.display(description=_("Método"), ordering="payment_method")
    def payment_method_display(self, obj):
        return obj.get_payment_method_display()

    @admin.display(description=_("Status"), ordering="payment_status")
    def payment_status_badge(self, obj):
        """Exibe o status de pagamento como badge colorido."""
        colors = {
            "paid": "#28a745",
            "pending": "#ffc107",
            "cancelled": "#6c757d",
        }
        color = colors.get(obj.payment_status, "#6c757d")
        text_color = "#fff" if obj.payment_status != "pending" else "#333"
        label = obj.get_payment_status_display()
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-size:11px;">'
            "{}</span>",
            color,
            text_color,
            label,
        )

    # ── Somatórios no rodapé da listagem ─────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        """
        Sobrescreve changelist_view para injetar somatórios de receita, despesa
        e saldo no contexto do template do admin.
        """
        response = super().changelist_view(request, extra_context=extra_context)

        try:
            # Obtém o queryset filtrado que já está na view
            qs = response.context_data["cl"].queryset
        except (AttributeError, KeyError):
            return response

        # Agrega receitas pagas
        totals = qs.filter(payment_status="paid").aggregate(
            total_income=Sum("amount", filter=Q(transaction_type="income")),
            total_expense=Sum("amount", filter=Q(transaction_type="expense")),
        )
        total_income = totals["total_income"] or Decimal("0.00")
        total_expense = totals["total_expense"] or Decimal("0.00")

        # Total pendente
        total_pending = (
            qs.filter(payment_status="pending").aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        response.context_data["summary"] = {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "total_pending": total_pending,
            "total_transactions": qs.count(),
        }
        return response
