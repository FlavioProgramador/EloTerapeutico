"""Listagens financeiras baseadas em selectors."""

from rest_framework.decorators import action
from rest_framework.response import Response

from ..selectors.transactions import (
    pending_transactions,
    unbilled_appointments_for,
)
from .serializers import TransactionListSerializer


class TransactionListActions:
    @action(detail=False, methods=["get"], url_path="pending")
    def pending(self, request):
        queryset = pending_transactions(
            user=request.user,
            patient_id=request.query_params.get("patient"),
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TransactionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(TransactionListSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="unbilled-appointments")
    def unbilled_appointments(self, request):
        queryset = unbilled_appointments_for(request.user)
        data = [
            {
                "id": appointment.id,
                "patient_id": appointment.patient_id,
                "patient_name": appointment.patient.full_name,
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,
                "session_value": str(appointment.session_value or "0.00"),
            }
            for appointment in queryset
        ]
        return Response(data)
