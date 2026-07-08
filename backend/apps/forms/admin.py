from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline

from .models import FormAnswer, FormField, FormSubmission, FormTemplate, TherapeuticForm


class FormFieldInline(TabularInline):
    model = FormField
    extra = 0
    fields = ("order", "type", "label", "required", "is_visible", "internal_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("order", "id")


@admin.register(FormTemplate)
class FormTemplateAdmin(ModelAdmin):
    list_display = ("name", "category", "is_system_template", "is_active", "updated_at")
    list_filter = ("category", "is_system_template", "is_active", "created_at", "updated_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Dados principais", {"fields": ("name", "description", "category", "icon")}),
        (
            "Estrutura",
            {
                "fields": ("fields_schema",),
                "description": "Schema JSON usado para gerar campos do formulário.",
            },
        ),
        ("Status", {"fields": ("is_system_template", "is_active")}),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TherapeuticForm)
class TherapeuticFormAdmin(ModelAdmin):
    list_display = ("name", "owner", "category", "status", "created_by", "updated_at")
    list_filter = ("category", "status", "created_at", "updated_at")
    search_fields = (
        "name",
        "description",
        "owner__email",
        "owner__full_name",
        "created_by__full_name",
    )
    autocomplete_fields = ("owner", "source_template", "created_by", "updated_by")
    list_select_related = ("owner", "source_template", "created_by", "updated_by")
    readonly_fields = ("created_at", "updated_at", "archived_at")
    inlines = [FormFieldInline]
    actions = ("action_archive_forms", "action_restore_forms")

    fieldsets = (
        (
            "Dados principais",
            {"fields": ("owner", "name", "description", "category", "status")},
        ),
        (
            "Origem e autoria",
            {"fields": ("source_template", "created_by", "updated_by")},
        ),
        (
            "Auditoria",
            {
                "fields": ("created_at", "updated_at", "archived_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Arquivar formulários selecionados")
    def action_archive_forms(self, request, queryset):
        if not request.user.has_perm("forms.change_therapeuticform"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for form in queryset.exclude(status=TherapeuticForm.Status.ARCHIVED):
            form.archive(request.user)
            count += 1
        self.message_user(request, f"{count} formulário(s) arquivado(s).", messages.WARNING)

    @admin.action(description="Restaurar formulários selecionados")
    def action_restore_forms(self, request, queryset):
        if not request.user.has_perm("forms.change_therapeuticform"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for form in queryset.filter(status=TherapeuticForm.Status.ARCHIVED):
            form.restore(request.user)
            count += 1
        self.message_user(request, f"{count} formulário(s) restaurado(s).", messages.SUCCESS)


@admin.register(FormSubmission)
class FormSubmissionAdmin(ModelAdmin):
    list_display = ("form", "owner", "patient", "status", "submitted_at", "created_at")
    list_filter = ("status", "submitted_at", "created_at")
    search_fields = ("form__name", "patient__full_name", "owner__email", "owner__full_name")
    autocomplete_fields = ("form", "owner", "patient", "professional", "submitted_by")
    raw_id_fields = ("appointment",)
    list_select_related = ("form", "owner", "patient", "professional", "submitted_by")
    readonly_fields = ("submitted_at", "created_at", "updated_at")
    actions = ("action_mark_reviewed", "action_archive_submissions")

    fieldsets = (
        (
            "Vínculos",
            {"fields": ("form", "owner", "patient", "professional", "appointment")},
        ),
        ("Status", {"fields": ("status", "submitted_by", "submitted_at")}),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.action(description="Marcar envios como revisados")
    def action_mark_reviewed(self, request, queryset):
        if not request.user.has_perm("forms.change_formsubmission"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        updated = queryset.update(status=FormSubmission.Status.REVIEWED)
        self.message_user(request, f"{updated} envio(s) revisado(s).", messages.SUCCESS)

    @admin.action(description="Arquivar envios selecionados")
    def action_archive_submissions(self, request, queryset):
        if not request.user.has_perm("forms.change_formsubmission"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        updated = queryset.update(status=FormSubmission.Status.ARCHIVED)
        self.message_user(request, f"{updated} envio(s) arquivado(s).", messages.WARNING)


@admin.register(FormAnswer)
class FormAnswerAdmin(ModelAdmin):
    list_display = ("submission", "field", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("field__label", "submission__form__name", "submission__patient__full_name")
    raw_id_fields = ("submission",)
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("submission", "field")

    fieldsets = (
        ("Vínculo", {"fields": ("submission", "field")}),
        ("Resposta", {"fields": ("value",)}),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
