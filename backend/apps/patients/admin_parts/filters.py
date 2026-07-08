"""Filtros customizados do admin de pacientes."""

from datetime import date

from django.contrib import admin

from ..models import Patient


class SoftDeletedFilter(admin.SimpleListFilter):
    """Filtro customizado para exibir pacientes ativos ou deletados."""

    title = "Situação no sistema"
    parameter_name = "soft_deleted"

    def lookups(self, request, model_admin):
        return [
            ("active", "Ativos"),
            ("deleted", "Arquivados"),
            ("all", "Todos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "deleted":
            return Patient.all_objects.filter(deleted_at__isnull=False)
        if self.value() == "all":
            return Patient.all_objects.all()
        return queryset.filter(deleted_at__isnull=True)


class IsMinorFilter(admin.SimpleListFilter):
    """Filtro para exibir apenas pacientes menores de 18 anos."""

    title = "Faixa etária"
    parameter_name = "is_minor"

    def lookups(self, request, model_admin):
        return [
            ("minor", "Menores de 18 anos"),
            ("adult", "Adultos (18+)"),
        ]

    def queryset(self, request, queryset):
        today = date.today()
        try:
            cutoff = today.replace(year=today.year - 18)
        except ValueError:
            cutoff = today.replace(year=today.year - 18, day=28)

        if self.value() == "minor":
            return queryset.filter(birth_date__gt=cutoff)
        if self.value() == "adult":
            return queryset.filter(birth_date__lte=cutoff)
        return queryset
