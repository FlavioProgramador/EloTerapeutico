"""
apps/patients/filters.py
Filtros de pesquisa para o app de Pacientes.
"""

from django_filters import rest_framework as filters
from .models import Patient


class PatientFilter(filters.FilterSet):
    """
    Filtros para busca de pacientes.
    Permite filtrar por status, terapeuta (apenas admin vê este filtro na prática),
    faixas de data de nascimento e data de cadastro.
    """
    birth_date_gte = filters.DateFilter(field_name="birth_date", lookup_expr="gte")
    birth_date_lte = filters.DateFilter(field_name="birth_date", lookup_expr="lte")
    
    created_at_gte = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    search = filters.CharFilter(method="filter_search", label="Buscar por Nome, CPF ou Telefone")

    class Meta:
        model = Patient
        fields = [
            "status",
            "therapist",
            "birth_date_gte",
            "birth_date_lte",
            "created_at_gte",
            "created_at_lte",
        ]

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        # Se for apenas dígitos, tenta buscar pelo CPF ou telefone
        digits_only = "".join(filter(str.isdigit, value))
        if digits_only:
            # Busca pelo CPF (exato ou contendo) ou telefone
            return queryset.filter(
                cpf__contains=digits_only
            ) | queryset.filter(
                phone__contains=digits_only
            ) | queryset.filter(
                full_name__icontains=value
            )
        # Se contiver letras, busca apenas pelo nome
        return queryset.filter(full_name__icontains=value)
