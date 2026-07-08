from django.contrib import admin

from .models import FormAnswer, FormField, FormSubmission, FormTemplate, TherapeuticForm


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ("order", "type", "label", "required", "is_visible")


@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_system_template", "is_active", "updated_at")
    list_filter = ("category", "is_system_template", "is_active")
    search_fields = ("name", "description")


@admin.register(TherapeuticForm)
class TherapeuticFormAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "category", "status", "created_by", "updated_at")
    list_filter = ("category", "status")
    search_fields = ("name", "description", "owner__email")
    inlines = [FormFieldInline]


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ("form", "owner", "patient", "status", "submitted_at", "created_at")
    list_filter = ("status",)
    search_fields = ("form__name", "patient__full_name", "owner__email")


@admin.register(FormAnswer)
class FormAnswerAdmin(admin.ModelAdmin):
    list_display = ("submission", "field", "updated_at")
    search_fields = ("field__label",)
