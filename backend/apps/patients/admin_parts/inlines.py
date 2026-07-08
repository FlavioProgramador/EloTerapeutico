"""Inlines do admin de pacientes."""

from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import TabularInline

from apps.agenda.models import Appointment
from apps.financeiro.models import FinancialTransaction


class AppointmentInline(TabularInline):
    model = Appointment
    extra = 0
    fields = ("therapist", "start_time", "end_time", "status", "session_value", "edit_link")
    readonly_fields = ("edit_link",)
    tab = True
    verbose_name = "Consulta"
    verbose_name_plural = "Consultas"

    def edit_link(self, obj):
        if obj.pk:
            url = reverse("admin:agenda_appointment_change", args=[obj.pk])
            return format_html(
                '<a href="{}" class="font-medium text-primary-600 dark:text-primary-500 hover:underline">Editar Completo</a>',
                url,
            )
        return "—"

    edit_link.short_description = "Ação"


class FinancialTransactionInline(TabularInline):
    model = FinancialTransaction
    extra = 0
    fields = ("therapist", "transaction_type", "category", "amount", "payment_status", "due_date", "edit_link")
    readonly_fields = ("edit_link",)
    tab = True
    verbose_name = "Transação Financeira"
    verbose_name_plural = "Transações Financeiras"

    def edit_link(self, obj):
        if obj.pk:
            url = reverse("admin:financeiro_financialtransaction_change", args=[obj.pk])
            return format_html(
                '<a href="{}" class="font-medium text-primary-600 dark:text-primary-500 hover:underline">Editar Completo</a>',
                url,
            )
        return "—"

    edit_link.short_description = "Ação"
