"""
apps/agenda/filters.py
Filtros de consulta para a agenda.
"""

from django_filters import rest_framework as filters
from .models import Appointment


class AppointmentFilter(filters.FilterSet):
    """
    Filtro para agendamentos.
    Permite filtrar por faixa de data (período), status, paciente e terapeuta.
    """
    start_time_gte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_time_lte = filters.IsoDateTimeFilter(field_name="start_time", lookup_expr="lte")

    class Meta:
        model = Appointment
        fields = [
            "status",
            "patient",
            "therapist",
            "start_time_gte",
            "start_time_lte",
            "is_recurring",
        ]
