"""Admin de pacotes de sessões."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.scheduling.models import PatientPackage


@admin.register(PatientPackage)
class PatientPackageAdmin(ModelAdmin):
    list_display = (
        "name",
        "patient",
        "therapist",
        "sessions_used",
        "sessions_contracted",
        "valid_until",
        "status",
    )
    list_filter = ("status", "therapist", "valid_until")
    search_fields = ("name", "patient__full_name", "therapist__full_name")
    list_select_related = ("patient", "therapist")
    autocomplete_fields = ("patient", "therapist")


__all__ = ["PatientPackageAdmin"]
